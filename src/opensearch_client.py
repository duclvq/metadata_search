from opensearchpy import OpenSearch

from src.config import settings

_client: OpenSearch | None = None


def get_client() -> OpenSearch:
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[{
                "host": settings.opensearch_host,
                "port": settings.opensearch_port,
            }],
            http_auth=(settings.opensearch_user, settings.opensearch_password),
            use_ssl = False,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False
        )
    return _client
