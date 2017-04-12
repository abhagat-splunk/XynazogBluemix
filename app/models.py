from flask import url_for
from werkzeug.exceptions import NotFound
from custom_exceptions import DataValidationError


class Pet(object):
    __redis = None

    def __init__(self, id=0, name=None, category=None):
        self.id = int(id)
        self.name = name
        self.category = category

    def self_url(self):
        return url_for('get_pets', id=self.id, _external=True)

    def save(self):
        if self.name == None:
            raise AttributeError('name attribute is not set')
        if self.id == 0:
            self.id = self.__next_index()
        Pet.__redis.hmset(self.id, self.serialize())

    def delete(self):
        Pet.__redis.delete(self.id)

    def __next_index(self):
        return Pet.__redis.incr('index')

    def serialize(self):
        return { "id": self.id, "name": self.name, "category": self.category }

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.category = data['category']
        except KeyError as e:
            raise DataValidationError('Invalid pet: missing ' + e.args[0])
        except TypeError as e:
            raise DataValidationError('Invalid pet: body of request contained bad or no data')
        return self

######################################################################
#  S T A T I C   D A T A B A S E   M E T H O D S
######################################################################

    @staticmethod
    def use_db(redis):
        Pet.__redis = redis

    @staticmethod
    def remove_all():
        Pet.__redis.flushall()

    @staticmethod
    def all():
        # results = [Pet.from_dict(redis.hgetall(key)) for key in redis.keys() if key != 'index']
        results = []
        for key in Pet.__redis.keys():
            if key != 'index':  # filer out our id index
                data = Pet.__redis.hgetall(key)
                pet = Pet(data['id']).deserialize(data)
                results.append(pet)
        return results

    @staticmethod
    def find(id):
        if Pet.__redis.exists(id):
            data = Pet.__redis.hgetall(id)
            pet = Pet(data['id']).deserialize(data)
            return pet
        else:
            return None

    @staticmethod
    def find_or_404(id):
        pet = Pet.find(id)
        if not pet:
            raise NotFound("Pet with id '{}' was not found.".format(id))
        return pet

    @staticmethod
    def find_by_category(category):
        # return [pet for pet in Pet.__data if pet.category == category]
        results = []
        for key in Pet.__redis.keys():
            if key != 'index':  # filer out our id index
                data = Pet.__redis.hgetall(key)
                if data['category'] == category:
                    results.append(Pet(data['id']).deserialize(data))
        return results