import os
from label_studio_sdk import Client
from .jwt import jwt_header

LABEL_STUDIO_DEFAULT_URL = 'http://label-studio'
LABEL_STUDIO_DEFAULT_API_KEY = 'DUMMY'

########## MONKEY PATCH ##############
def init(
        self,
        url: str = None,
        api_key: str = LABEL_STUDIO_DEFAULT_API_KEY,
        session=None,
        extra_headers: dict = None,
        cookies: dict = None,
        versions=None,
        make_request_raise=True,
):
    """Initialize the client the Teknoir way!. Do this before using other Label Studio SDK classes and methods in your script.

    Parameters
    ----------
    url: str
        Label Studio host address.
        Example: http://localhost:8080
    api_key: str
        Not used.
    session: requests.Session()
        If None, a new one is created.
    extra_headers: dict
        Additional headers that will be passed to each http request
    cookies: dict
        Cookies that will be passed to each http request.
    versions: dict
        Versions of Label Studio components for the connected instance
    make_request_raise: bool
        If true, make_request will raise exceptions on request errors
    """
    if not url:
        url = os.getenv('LABEL_STUDIO_URL', LABEL_STUDIO_DEFAULT_URL)
    self.url = url.rstrip('/')
    self.make_request_raise = make_request_raise
    self.session = session or self.get_session()

    self.api_key = api_key

    self.headers = {}
    if extra_headers:
        self.headers.update(extra_headers)

    # set cookies
    self.cookies = cookies

    # set versions from /version endpoint
    self.versions = versions if versions else self.get_versions()
    self.is_enterprise = 'label-studio-enterprise-backend' in self.versions


Client.__init__ = init
########## MONKEY PATCH ##############

__version__ = '0.0.1'
