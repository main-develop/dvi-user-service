import itertools

from drf_spectacular.drainage import warn
from drf_spectacular.plumbing import build_media_type_object
from drf_spectacular.utils import OpenApiRequest
from drf_standardized_errors.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    def _get_request_body(self, direction="request"):
        """
        Override the base method to add DELETE to the tuple of methods that
        can have a body, since the application logic requires passwords to be
        passed in the body of the DELETE request.
        """
        # only unsafe methods can have a body, including DELETE
        if self.method not in ("PUT", "PATCH", "POST", "DELETE"):
            return None

        request_serializer = self.get_request_serializer()
        request_body_required = True
        content = []

        # either implicit media-types via available parsers
        # or manual list via decoration
        if isinstance(request_serializer, dict):
            media_types_iter = request_serializer.items()
        else:
            media_types_iter = zip(
                self.map_parsers(), itertools.repeat(request_serializer)
            )

        for media_type, serializer in media_types_iter:
            if isinstance(serializer, OpenApiRequest):
                serializer, examples, encoding = (
                    serializer.request,
                    serializer.examples,
                    serializer.encoding,
                )
            else:
                encoding, examples = None, None

            if (
                encoding
                and media_type != "application/x-www-form-urlencoded"
                and not media_type.startswith("multipart")
            ):
                warn(
                    "Encodings object on media types other than"
                    "'application/x-www-form-urlencoded'"
                    "or 'multipart/*' have undefined behavior."
                )

            examples = self._get_examples(
                serializer, direction, media_type, None, examples
            )
            schema, partial_request_body_required = self._get_request_for_media_type(
                serializer, direction
            )

            if schema is not None:
                content.append((media_type, schema, examples, encoding))
                request_body_required &= partial_request_body_required

        if not content:
            return None

        request_body = {
            "content": {
                media_type: build_media_type_object(schema, examples, encoding)
                for media_type, schema, examples, encoding in content
            }
        }
        if request_body_required:
            request_body["required"] = request_body_required
        return request_body
