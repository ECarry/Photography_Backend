from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Photo(models.Model):
    title = models.CharField(null=True, blank=True, max_length=255)
    image = models.ImageField(upload_to='photos/%Y/%m/%d/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    thumbnail = models.ImageField(null=True, blank=True, upload_to='photos/thumbnails/%Y/%m/%d/')
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True, verbose_name='拍摄时间')
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    thumbnail_width = models.IntegerField(blank=True, null=True)
    thumbnail_height = models.IntegerField(blank=True, null=True)
    # 读取照片元数据为十进制
    lat = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6, verbose_name='纬度')
    lon = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6, verbose_name='经度')
    altitude = models.FloatField(null=True, blank=True, verbose_name='海拔')
    aperture = models.FloatField(null=True, blank=True, verbose_name='光圈')
    iso = models.IntegerField(null=True, blank=True)
    shutter_speed = models.CharField(null=True, blank=True, max_length=100)
    focal_length = models.FloatField(null=True, blank=True, verbose_name='焦距')
    rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True, verbose_name='评分')
    camera_brand = models.CharField(null=True, blank=True, max_length=100)
    camera_model = models.CharField(null=True, blank=True, max_length=100)
    camera_lens = models.CharField(null=True, blank=True, max_length=100)
    hash = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return self.title


class Video(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    video_file = models.FileField(upload_to='videos/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
