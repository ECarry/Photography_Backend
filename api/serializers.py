from rest_framework import serializers
from .models import Photo, PhotoCategory, Video


class PhotoSerializer(serializers.ModelSerializer):
    categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = Photo
        fields = '__all__'


class PhotoCategorySerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True)

    class Meta:
        model = PhotoCategory
        fields = '__all__'


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'
