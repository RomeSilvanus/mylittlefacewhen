#from django.core.paginator import Paginator, InvalidPage
#from django.conf.urls.defaults import url
#from django.http import Http404
from tastypie.resources import ModelResource, Resource
from tastypie.api import Api
from tastypie.utils import trailing_slash
from tastypie import fields
from tagging.models import Tag
from viewer import models
from tastypie.constants import ALL
from tastypie.exceptions import BadRequest

from viewer.api import auths

from viewer import forms

import datetime
import json
import random

API = Api(api_name="v2")

MEDIA = "/media/"

FACES_LEN = -1

class FaceResource(ModelResource):
    tags = fields.ToManyField('viewer.api.v2.TagResource', 'tags', full=True, null=True)
    class Meta:
        queryset = models.Face.objects.all()
        max_limit = 1000
        allowed_methods = ('get', 'post', 'put', 'delete', )
        filtering = {
                "accepted": ("exact",),
                }
        ordering = ("id",)
        excludes = ("views", "comment", "removed", "gif", "png", "jpg", "webp", "small", "medium", "large", "huge", )
        authorization = auths.AnonMethodAllowed().set_allowed(["GET", "POST", "PUT"])

    def get_object_list(self, request):
        if request.GET.get("search"):
            try:
                tags = json.loads(request.GET.get("search", "[]"))
            except:
                raise BadRequest("Invalid tags")

            real_tags = [tag.strip() for tag in tags]

            objects = models.Face.tagged.with_all(real_tags)
        else:
            objects = super(FaceResource, self).get_object_list(request)

        return objects
    
    def apply_sorting(self, obj_list, options=None):
        global FACES_LEN
        if options.get("order_by") == "random":
            limit = int(options.get("limit", 1))
            if limit > 5:
                raise BadRequest("at most 5 randoms at a time")

            obj_list = obj_list.filter(accepted=True)
            if options.get("search"):
                faces_len = len(obj_list)
            else:
                if FACES_LEN == -1 or random.randint(0, 1000) > 999:
                    FACES_LEN = len(obj_list)
                faces_len = FACES_LEN
           
            if limit >= faces_len:
                return obj_list
            else:
                i = random.randint(0, faces_len - 1- limit)
                orders = ["id", "-id", "source", "-source", "width", "-width", "height", "-height"]
                return obj_list.order_by(random.choice(orders))[i:i+limit + 1]

        return super(FaceResource, self).apply_sorting(obj_list, options)


    def dehydrate(self, bundle):

        bundle.data["thumbnails"] = {}
        for itm in ("png", "jpg", "webp", "gif"):
            if getattr(bundle.obj, itm):
                bundle.data["thumbnails"][itm] = MEDIA + str(getattr(bundle.obj, itm))

        bundle.data["resizes"] = {}
        for itm in ("small", "medium", "large", "huge"):
            if getattr(bundle.obj, itm):
                bundle.data["resizes"][itm] = MEDIA + str(getattr(bundle.obj, itm))        

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        tags = ""
        for tag in bundle.data.get("tags"):
            tags += tag["name"] + ", "


        face = models.Face.objects.get(pk=bundle.data["id"])
        
        return face.public_update({"tags":tags, "source":bundle.data.get("source", "")})

    def obj_create(self, bundle, request=None, **kwargs):
        form = forms.CreateFace(bundle.data)
        if form.is_valid():
            return models.Face.submit(**form.cleaned_data)
        else:
            raise BadRequest("I just don't know what went wrong")


API.register(FaceResource())


class TagResource(ModelResource):
    class Meta:
        queryset = Tag.objects.all()
        include_resource_uri = False
        max_limit = 10000
        allowed_methods = ('get', )
        fields = ('name', )
        filtering = {
                "name": ("contains","startswith",),
                }

        
API.register(TagResource())


class FeedbackResource(ModelResource):
    class Meta:
        queryset = models.Feedback.objects.all()
        include_resource_uri = False
        filtering = {
                "processed": ("exact",),
                }
        ordering = ("id", "processed", )
        authorization = auths.AnonMethodAllowed().set_allowed(["POST"])

    def obj_create(self, bundle, request=None, **kwargs):
        feedback = {
            "text": bundle.data["feedback"],
            "contact": bundle.data.get("contact"),
            "useragent": request.META.get("HTTP_USER_AGENT", ""),
            }
        form = forms.FeedbackForm(feedback)
        
        if form.is_valid():
            bundle = super(FeedbackResource, self).obj_create(bundle, request, **kwargs)
            bundle.data = form.cleaned_data 

            for key, value in form.cleaned_data.iteritems():
                setattr(bundle.obj, key, value)
            
            bundle.obj.save()
            return bundle
        else:
            raise BadRequest("I just don't know what went wrong")

API.register(FeedbackResource())

class DetectResource(Resource):
    class Meta:
        include_resource_uri = False
        allowed_methods = ('get',)

    def get_list(self, request=None, **kwargs):
        filename = request.GET.get("filename")
        if filename:
            source, tags = models._detectSource(filename)
        else:
            raise BadRequest("Invalid tags")
        return self.create_response(request, {"source":source, "tags": tags })

API.register(DetectResource())

class FlagResource(ModelResource):
    class Meta:
        queryset = models.Flag.objects.all()
        include_resource_uri = False
        ordering = ("id", )
        authorization = auths.AnonMethodAllowed().set_allowed(["POST"])
        allowed_methods = ('post',)


    def obj_create(self, bundle, request=None, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        face_id = request.META.get("HTTP_REFERER").strip("/")
        reason = bundle.data.get("reason")
        if not all((face_id, reason)):
            raise BadRequest(": referer or report not included")
        
        try:
            face_id = int(face_id.rpartition("/")[2])
            face = models.Face.objects.get(id=face_id)
        except:
            raise BadRequest(": couldn't detect the page you're on")

        flag = models.Flag(
                face=face,
                user_agent=user_agent, 
                reason=reason
                )
        flag.save()
        return flag

API.register(FlagResource())

class AdResource(ModelResource):
    class Meta:
        queryset = models.Advert.objects.all()
        allowed_mathods = ('get',)
        include_resource_uri = False

    def apply_sorting(self, obj_list, options=None):
        i = random.randint(0, len(obj_list) - 1)
        return obj_list[i:i+1]

API.register(AdResource())
