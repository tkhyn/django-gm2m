from django.core.serializers import xml_serializer
from django.utils.encoding import smart_text
from django.utils import six

from ..fields import GM2MField
from ..contenttypes import ct, get_content_type


class Serializer(xml_serializer.Serializer):
    """
    xml_serializer.Serializer uses a different handle_m2m_field than
    python.Serializer, we therefore need to redefine it here
    """

    def handle_m2m_field(self, obj, field):

        if not isinstance(field, GM2MField):
            # use normal serialization from superclass
            super(Serializer, self).handle_m2m_field(obj, field)

        if field.remote_field.through._meta.auto_created:
            self._start_relational_field(field)
            if self.use_natural_foreign_keys:
                def handle_gm2m(value):
                    try:
                        natural = value.natural_key()
                        use_natural_key = True
                    except AttributeError:
                        natural = smart_text(value._get_pk_val())
                        use_natural_key = False

                    # Iterable natural keys are rolled out as subelements
                    if use_natural_key:
                        attrs = {'pk': smart_text(value._get_pk_val())}
                    else:
                        attrs = {}

                    self.xml.startElement("object", attrs)

                    # add content type information
                    app, model = get_content_type(value).natural_key()
                    self.xml.addQuickElement('contenttype', attrs={
                        'app': app,
                        'model': model
                    })

                    if use_natural_key:
                        for key_value in natural:
                            self.xml.startElement("natural", {})
                            self.xml.characters(smart_text(key_value))
                            self.xml.endElement("natural")

                    self.xml.endElement("object")
            else:
                def handle_gm2m(value):
                    self.xml.startElement('object', {
                        'pk': smart_text(value._get_pk_val())
                    })

                    # add content type information
                    app, model = get_content_type(value).natural_key()
                    self.xml.addQuickElement('contenttype', attrs={
                        'app': app,
                        'model': model
                    })

                    self.xml.endElement('object')

            for relobj in getattr(obj, field.name).iterator():
                handle_gm2m(relobj)

            self.xml.endElement("field")


class Deserializer(xml_serializer.Deserializer):

    def _handle_m2m_field_node(self, node, field):
        """
        Handle a <field> node for a GM2MField
        """

        if not isinstance(field, GM2MField):
            return super(Deserializer, self)._handle_m2m_field_node(node, field)

        objs = []
        for obj_node in node.getElementsByTagName('object'):
            natural = obj_node.getElementsByTagName('natural')

            # extract contenttype
            ct_node = obj_node.getElementsByTagName('contenttype')[0]

            model = ct.ContentType.objects.get_by_natural_key(
                ct_node.getAttribute('app'), ct_node.getAttribute('model')
            ).model_class()
            mngr = model._default_manager.db_manager(self.db)


            if natural:
                # extract natural keys
                key = [xml_serializer.getInnerText(k).strip() for k in natural]
            else:
                # normal value
                key = obj_node.getAttribute('pk')

            if hasattr(model._default_manager, 'get_by_natural_key'):
                if hasattr(key, '__iter__') \
                and not isinstance(key, six.text_type):
                    obj = mngr.get_by_natural_key(*key)
                else:
                    obj = mngr.get_by_natural_key(key)
            else:
                obj = mngr.get(pk=key)

            objs.append(obj)

        return objs
