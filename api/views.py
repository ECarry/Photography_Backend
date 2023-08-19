import os
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Category, Photo, Video, Album
from .serializers import CategorySerializer, PhotoSerializer, VideoSerializer, AlbumSerializer
import io
import re
from datetime import datetime
from PIL import Image
from rest_framework import viewsets, serializers, status
import exifread
import blurhash


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    #permission_classes = [IsAuthenticatedOrReadOnly]


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    #permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Album.objects.all()
        category = self.request.query_params.get('category')

        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 获取相册下的所有照片并删除
        photos = Photo.objects.filter(album=instance)
        for photo in photos:
            self.delete_photo(photo)

        # 删除相册封面文件
        if instance.cover_photo:
            self.delete_cover_photo(instance.cover_photo)

        # 删除相册记录
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete_photo(self, photo):
        # 删除上传的图片
        if photo.image:
            path = os.path.join(settings.MEDIA_ROOT, str(photo.image))
            os.remove(path)

        # 删除略缩图
        if photo.thumbnail:
            thumbnail_path = os.path.join(settings.MEDIA_ROOT, str(photo.thumbnail))
            os.remove(thumbnail_path)

        # 删除照片记录
        photo.delete()

    def delete_cover_photo(self, cover_photo):
        # 删除相册封面文件
        path = os.path.join(settings.MEDIA_ROOT, str(cover_photo))
        os.remove(path)


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-id')
    serializer_class = PhotoSerializer

    # permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        album = self.request.data.get('album')
        category = self.request.data.get('category')

        # 如果提供了相册 ID，执行相册验证
        if album:
            album = Album.objects.get(pk=album)
            if album.category_id != int(category):
                raise serializers.ValidationError("Photo's category must match album's category.",
                                                  code=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data.pop('image')
        size_tags = {}
        # 保存原图长宽尺寸
        with Image.open(image_file) as img:
            size_tags['width'], size_tags['height'] = img.size
        exif_tags = self.get_exif_data(image_file)
        thumbnail = self.create_thumbnail(image_file)
        # hash
        hash_code = blurhash.encode(thumbnail, x_components=4, y_components=3)

        # 保存略缩图长宽尺寸
        with Image.open(thumbnail) as thumbnail_img:
            size_tags['thumbnail_width'], size_tags['thumbnail_height'] = thumbnail_img.size
        photo = serializer.save(**exif_tags, **size_tags, title=image_file.name, hash=hash_code)
        photo.image.save(image_file.name, image_file, save=True)
        photo.thumbnail.save(thumbnail.name, thumbnail, save=True)

    def get_queryset(self):
        queryset = Photo.objects.all().order_by('-id')
        category = self.request.query_params.get('category')
        album = self.request.query_params.get('album')

        if category:
            queryset = queryset.filter(category=category)

        if album:
            queryset = queryset.filter(album_id=album)

        return queryset

    def perform_destroy(self, instance):
        # 删除上传的图片
        if instance.image:
            path = os.path.join(settings.MEDIA_ROOT, str(instance.image))
            os.remove(path)

        # 删除略缩图
        if instance.thumbnail:
            thumbnail_path = os.path.join(settings.MEDIA_ROOT, str(instance.thumbnail))
            os.remove(thumbnail_path)

        # 删除数据库记录
        instance.delete()

    # chatGPT 优化后的代码
    def get_exif_data(self, image_file):
        exif_tags = {}
        tags = exifread.process_file(image_file, stop_tag='TAG')
        if tags:
            fields_to_format = {
                'EXIF DateTimeOriginal': 'timestamp',
                'EXIF FNumber': 'aperture',
                'EXIF FocalLengthIn35mmFilm': 'focal_length',
                'EXIF ISOSpeedRatings': 'iso',
                'EXIF ExposureTime': 'shutter_speed',
                'Image Make': 'camera_brand',
                'Image Model': 'camera_model',
                'EXIF LensModel': 'camera_lens',
                'GPS GPSAltitude': 'altitude'
            }
            for tag, field in fields_to_format.items():
                value = str(tags.get(tag))
                if value != 'None':
                    if field == 'timestamp':
                        timestamp_obj = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                        exif_tags[field] = formatted_timestamp
                    elif field == 'aperture' or field == 'focal_length' or field == 'altitude':
                        exif_tags[field] = self.calc_num(value)
                    elif field == 'camera_model' and value == 'FC3411':
                        exif_tags[field] = 'Air 2S'
                    else:
                        exif_tags[field] = value

            lat_tag = tags.get('GPS GPSLatitude')
            lat_ref = tags.get('GPS GPSLatitudeRef')
            lon_tag = tags.get('GPS GPSLongitude')
            lon_ref = tags.get('GPS GPSLongitudeRef')

            # Convert the latitude and longitude tags to decimal format
            if lat_tag and lat_ref and lon_tag and lon_ref:
                lat = self.get_decimal_from_dms(lat_tag.values, lat_ref.values)
                lon = self.get_decimal_from_dms(lon_tag.values, lon_ref.values)
                exif_tags['lat'] = lat
                exif_tags['lon'] = lon
        return exif_tags

    # 判断获取的数据是否为数字或者 a/b
    def calc_num(self, string):
        pattern = re.compile(r'(\d+)/(\d+)')
        match = pattern.search(string)
        if match:
            a, b = map(float, match.groups())
            return a / b
        else:
            return float(string)

    # 经纬度 DMS 转换
    def get_decimal_from_dms(self, dms, ref):
        degrees = dms[0].num / dms[0].den
        minutes = dms[1].num / dms[1].den / 60.0
        seconds = dms[2].num / dms[2].den / 3600.0
        if ref in ['S', 'W']:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds
        return degrees + minutes + seconds

    # 创建略缩图
    def create_thumbnail(self, image_file):
        with Image.open(image_file) as img:
            # 获取原尺寸等比压缩
            width, height = img.size
            aspect_ratio = height / width
            new_height = int(1080 * aspect_ratio)
            new_size = (1080, new_height)
            img.thumbnail(new_size)
            thumbnail_file = io.BytesIO()
            img.save(thumbnail_file, format='JPEG')
            thumbnail_file.name = image_file.name
            # 将文件指针（读写位置）移动到文件的开头，以便从文件的开头读取数据。
            thumbnail_file.seek(0)
            return thumbnail_file


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
