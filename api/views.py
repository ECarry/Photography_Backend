from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Category, Photo, Video
from .serializers import CategorySerializer, PhotoSerializer, VideoSerializer
import io
import re
from datetime import datetime
from PIL import Image
from rest_framework import viewsets, status
import exifread


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        print('---------self--------', self.request.data.get('category'))

        image_file = serializer.validated_data.pop('image')
        exif_tags = self.get_exif_data(image_file)
        photo = serializer.save(**exif_tags, title=image_file.name)
        thumbnail = self.create_thumbnail(image_file)
        photo.image.save(image_file.name, image_file, save=True)
        photo.thumbnail.save(thumbnail.name, thumbnail, save=True)

    # 从上传的图片获取元数据
    def get_exif_data(self, image_file):
        exif_tags = {}
        tags = exifread.process_file(image_file, stop_tag='TAG')
        if tags:
            # 格式化时间
            timestamp = str(tags.get('EXIF DateTimeOriginal'))
            timestamp_obj = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
            formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
            exif_tags['timestamp'] = formatted_timestamp
            # 格式化光圈环
            aperture = str(tags.get('EXIF FNumber'))
            if aperture:
                exif_tags['aperture'] = self.calc_num(aperture)
            # 格式化焦距
            focal_length = str(tags.get('EXIF FocalLengthIn35mmFilm'))
            if focal_length:
                exif_tags['focal_length'] = self.calc_num(focal_length)
            exif_tags['iso'] = str(tags.get('EXIF ISOSpeedRatings'))
            exif_tags['shutter_speed'] = str(tags.get('EXIF ExposureTime'))
            exif_tags['camera_brand'] = str(tags.get('Image Make'))
            exif_tags['camera_model'] = str(tags.get('Image Model'))
            exif_tags['camera_lens'] = str(tags.get('EXIF LensModel'))

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
            img.thumbnail((300, 300))
            thumbnail_file = io.BytesIO()
            img.save(thumbnail_file, format='JPEG')
            thumbnail_file.name = image_file.name
            # 将文件指针（读写位置）移动到文件的开头，以便从文件的开头读取数据。
            thumbnail_file.seek(0)
            return thumbnail_file


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]
