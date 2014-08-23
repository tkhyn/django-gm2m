from django.contrib.contenttypes.generic import GenericRel


class GM2MRel(GenericRel):

    def __init__(self, field, to, through=None):

        super(GM2MRel, self).__init__(field, to)

        self.multiple = True
        self.through = through

    def get_related_field(self):
        """
        Returns the field in the to object to which this relationship is tied
        (this is always the primary key on the target model).
        """
        return self.to._meta.pk
