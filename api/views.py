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
        image_file = serializer.validated_data.pop('image')
        exif_tags = self.get_exif_data(image_file)
        photo = serializer.save(**exif_tags, title=image_file.name)
        thumbnail = self.create_thumbnail(image_file)
        photo.image.save(image_file.name, image_file, save=True)
        photo.thumbnail.save(thumbnail.name, thumbnail, save=True)

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
                'EXIF LensModel': 'camera_lens'
            }
            for tag, field in fields_to_format.items():
                value = str(tags.get(tag))
                if value != 'None':
                    if field == 'timestamp':
                        timestamp_obj = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                        exif_tags[field] = formatted_timestamp
                    elif field == 'aperture' or field == 'focal_length':
                        exif_tags[field] = self.calc_num(value)
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

    # 从上传的图片获取元数据
    # def get_exif_data(self, image_file):
    #     exif_tags = {}
    #     tags = exifread.process_file(image_file, stop_tag='TAG')
    #     if tags:
    #         # 格式化时间
    #         timestamp = str(tags.get('EXIF DateTimeOriginal'))
    #         if timestamp != 'None':
    #             timestamp_obj = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
    #             formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
    #             exif_tags['timestamp'] = formatted_timestamp
    #         else:
    #             now = datetime.now()  # 获取当前时间
    #             formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")  # 格式化时间为指定字符串格式
    #             exif_tags['timestamp'] = formatted_date
    #
    #         # 格式化光圈环
    #         aperture = str(tags.get('EXIF FNumber'))
    #         if aperture != 'None':
    #             exif_tags['aperture'] = self.calc_num(aperture)
    #
    #         # 格式化焦距
    #         focal_length = str(tags.get('EXIF FocalLengthIn35mmFilm'))
    #         if focal_length != 'None':
    #             exif_tags['focal_length'] = self.calc_num(focal_length)
    #
    #         iso = str(tags.get('EXIF ISOSpeedRatings'))
    #         if iso != 'None':
    #             exif_tags['iso'] = iso
    #
    #         shutter_speed = str(tags.get('EXIF ExposureTime'))
    #         if shutter_speed != 'None':
    #             exif_tags['shutter_speed'] = shutter_speed
    #
    #         camera_brand = str(tags.get('Image Make'))
    #         if camera_brand != 'None':
    #             exif_tags['camera_brand'] = camera_brand
    #
    #         camera_model = str(tags.get('Image Model'))
    #         if camera_model != 'None':
    #             exif_tags['camera_model'] = camera_model
    #
    #         camera_lens = str(tags.get('EXIF LensModel'))
    #         if camera_lens != 'None':
    #             exif_tags['camera_lens'] = camera_lens
    #
    #         lat_tag = tags.get('GPS GPSLatitude')
    #         lat_ref = tags.get('GPS GPSLatitudeRef')
    #         lon_tag = tags.get('GPS GPSLongitude')
    #         lon_ref = tags.get('GPS GPSLongitudeRef')
    #
    #         # Convert the latitude and longitude tags to decimal format
    #         if lat_tag and lat_ref and lon_tag and lon_ref:
    #             lat = self.get_decimal_from_dms(lat_tag.values, lat_ref.values)
    #             lon = self.get_decimal_from_dms(lon_tag.values, lon_ref.values)
    #             exif_tags['lat'] = lat
    #             exif_tags['lon'] = lon
    #     return exif_tags

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
    # permission_classes = [IsAuthenticatedOrReadOnly]
