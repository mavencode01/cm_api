# Copyright (c) 2011-2012 Cloudera, Inc. All rights reserved.

try:
  import json
except ImportError:
  import simplejson as json

__docformat__ = "epytext"


class BaseApiObject(object):
  """
  The BaseApiObject helps with (de)serialization from/to JSON.
  To take advantage of it, the derived class needs to define

  RW_ATTR - A list of mutable attributes
  RO_ATTR - A list of immutable attributes

  The derived class's ctor must take all the RW_ATTR as arguments.
  When de-serializing from JSON, all attributes will be set. Their
  names are taken from the keys in the JSON object.

  Reference objects (e.g. hostRef, clusterRef) are automatically
  deserialized. They can be accessed as attributes.
  """
  RO_ATTR = ( )         # Derived classes should define this
  RW_ATTR = ( )         # Derived classes should define this

  def __init__(self, **rw_attrs):
    for k, v in rw_attrs.items():
      if k not in self.RW_ATTR:
        raise ValueError("Unexpected ctor argument '%s' in %s" %
                         (k, self.__class__.__name__))
      self._setattr(k, v)

  @staticmethod
  def ctor_helper(self=None, **kwargs):
    """
    Note that we need a kw arg called `self'. The callers typically just
    pass their locals() to us.
    """
    BaseApiObject.__init__(self, **kwargs)

  def _setattr(self, k, v):
    """Set an attribute. We take care of instantiating reference objects."""
    # We play tricks when we notice that the attribute `k' ends with `Ref'.
    # We treat it as a reference object, i.e. another object to be deserialized.
    if isinstance(v, dict) and k.endswith("Ref"):
      # A reference, `v' should be a json dictionary
      cls_name = "Api" + k[0].upper() + k[1:]
      cls = globals()[cls_name]
      v = cls(**v)
    setattr(self, k, v)

  def to_json_dict(self):
    dic = { }
    for attr in self.RW_ATTR:
      value = getattr(self, attr)
      try:
        # If the value has to_json_dict(), call it
        value = value.to_json_dict()
      except AttributeError, ignored:
        pass
      dic[attr] = value
    return dic

  @classmethod
  def from_json_dict(cls, dic):
    rw_dict = { } 
    for k, v in dic.items():
      if k in cls.RW_ATTR:
        rw_dict[k] = v
        del dic[k]
    # Construct object based on RW_ATTR
    obj = cls(**rw_dict)

    # Initialize all RO_ATTR to be None
    for attr in cls.RO_ATTR:
      obj._setattr(attr, None)

    # Now set the RO_ATTR based on the json
    for k, v in dic.items():
      if k in cls.RO_ATTR:
        obj._setattr(k, v)
      else:
        raise KeyError("Unexpected attribute '%s' in %s json" %
                       (k, cls.__name__))
    return obj


class ApiList(object):
  """A list of some api object"""
  LIST_KEY = "items"

  def __init__(self, objects, count=None):
    self.objects = objects
    if count is None:
      self.count = len(objects)
    else:
      self.count = count

  def to_json_dict(self):
    return { ApiList.LIST_KEY :
            [ x.to_json_dict() for x in self.objects ] }

  def __len__(self):
    return self.objects.__len__()

  def __iter__(self):
    return self.objects.__iter__()

  def __getitem__(self, i):
    return self.objects.__getitem__(i)

  def __getslice(self, i, j):
    return self.objects.__getslice__(i, j)

  @staticmethod
  def from_json_dict(member_cls, dic):
    json_list = dic[ApiList.LIST_KEY]
    objects = [ member_cls.from_json_dict(x) for x in json_list ]
    return ApiList(objects, dic['count'])


#
# In order for BaseApiObject to automatically instantiate reference objects,
# it's more convenient for the reference classes to be defined here.
#

class ApiHostRef(BaseApiObject):
  RW_ATTR = ('hostId',)
  def __init__(self, hostId):
    BaseApiObject.ctor_helper(**locals())

class ApiServiceRef(BaseApiObject):
  RW_ATTR = ('clusterName', 'serviceName')
  def __init__(self, clusterName, serviceName):
    BaseApiObject.ctor_helper(**locals())

class ApiClusterRef(BaseApiObject):
  RW_ATTR = ('clusterName',)
  def __init__(self, clusterName):
    BaseApiObject.ctor_helper(**locals())
