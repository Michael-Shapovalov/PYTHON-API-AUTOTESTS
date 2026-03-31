import requests


class ProcessTemplateApiClient:
    """HTTP client for ProcessTemplate API methods."""

    JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
    ACCEPT_JSON = {"Accept": "application/json"}

    @staticmethod
    def create_or_update(put_url, payload=None, auth=None, raw_body=None, timeout=30):
        if raw_body is not None:
            return requests.put(
                put_url, data=raw_body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
            )
        return requests.put(
            put_url, json=payload, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
        )

    @staticmethod
    def create_or_update_many(base_url, payloads=None, auth=None, raw_body=None, timeout=30):
        url = f"{base_url.rstrip('/')}/ProcessTemplate/CreateOrUpdateMany"
        if raw_body is not None:
            return requests.put(
                url,
                data=raw_body,
                auth=auth,
                headers=ProcessTemplateApiClient.JSON_HEADERS,
                timeout=timeout,
            )
        return requests.put(
            url, json=payloads, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
        )

    @staticmethod
    def get_processtemplate(get_url, auth=None, page_num=0, page_size=0, no_count=False, timeout=30):
        params = {"pageNum": page_num, "pageSize": page_size, "noCount": no_count}
        return requests.get(
            get_url,
            params=params,
            auth=auth,
            headers=ProcessTemplateApiClient.ACCEPT_JSON,
            timeout=timeout,
        )

    @staticmethod
    def post_processtemplate(post_url, body, auth=None, raw_body=None, timeout=30):
        if raw_body is not None:
            return requests.post(
                post_url, data=raw_body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
            )
        return requests.post(
            post_url, json=body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
        )

    @staticmethod
    def delete(base_url, body, auth=None, raw_body=None, timeout=30):
        url = f"{base_url.rstrip('/')}/ProcessTemplate/Delete"
        if raw_body is not None:
            return requests.patch(
                url, data=raw_body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
            )
        return requests.patch(
            url, json=body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
        )

    @staticmethod
    def delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
        url = f"{base_url.rstrip('/')}/ProcessTemplate/DeleteMany"
        if raw_body is not None:
            return requests.patch(
                url, data=raw_body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
            )
        return requests.patch(
            url, json=body, auth=auth, headers=ProcessTemplateApiClient.JSON_HEADERS, timeout=timeout
        )

