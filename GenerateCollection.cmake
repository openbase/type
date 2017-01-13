# The following variables need to be set:
# SINGULAR_TYPE: Name of the type contained in the collection
# SINGULAR_TYPE_FILE_REL: relative path to the file containing the type for which the collection shall be created. Relative to the usual proto hierarchy in RST without domain. Used for include statements
# COLLECTION_TYPE: Name of the data type for the collection
# PACKAGE: the dotted package name of the target type
# OUT: File name (and path) of the generated collection type

MESSAGE("Creating ${OUT}")

CONFIGURE_FILE(
    proto/Collection.proto.in
    "${OUT}"
    @ONLY)
