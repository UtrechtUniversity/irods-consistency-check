class ResourceInterface:
    def check_object_exists(self, path):
        raise Exception("Not implemented")

    def check_coll_exists(self, path):
        raise Exception("Not implemented")

    def get_size(self, path):
        raise Exception("Not implemented")

    def get_checksum(self, path, checksumtype):
        raise Exception("Not implemented")
