=================
Auth0 and Mozilla
=================

Summary
=======

This implements Auth0 authentication that enforces Mozilla's Auth0 required
approach, but is flexible to work with your Django site.

It incorporates a pipeline that lets you orchestrate post-Auth0-login actions
letting you explicitly define how ah Auth0 identity matches your Django users,
adding additional rules for Auth0 identities, generating profiles, adding
additional metadata, etc.


Specs
=====

* (public): https://wiki.mozilla.org/Security/Guidelines/OpenID_Connect
* (public, session handling): https://wiki.mozilla.org/Security/Guidelines/OpenID_Connect#Implement_authentication_with_OpenID_Connect_.28OIDC.29_securely_in_my_web_applications_.28RP.29


Requirements
============

* Python 3
* Django 1.8+
* A caching backend (locmem if you've got only one node and one process,
  memcached or something real otherwise)


Configuration
=============

``AUTH0_CLIENT_ID``
   str: Your Auth0 client id. This is "public-ish".

``AUTH0_CLIENT_SECRET``
   str: Your Auth0 client secret. This is **NOT** public. Don't put this in version
   control, print it out anywhere, put it in your templates, log it, etc.

``AUTH0_DOMAIN``
   str: Domain for Auth0 login page.

   For example, I set up an app with Auth0 and the domain they gave me is
   ``willkg.auth0.com``.

   Mozilla uses ``auth.mozilla.auth0.com``.

``AUTH0_LOGIN_URL``
   str: This is the complete url to the Auth0 login page. It allows for variables
   so you don't have to have things in your settings file/environment multiple
   times. It will urlencode the values.

   Variables:

   * ``AUTH0_DOMAIN`` -- from settings
   * ``AUTH0_CLIENT_ID`` -- from settings
   * ``AUTH0_CALLBACK_URL`` -- from settings
   * ``STATE`` -- generated and stored in the request session and compared
     against later in the flow

   For example, the one I use for my app is::

      https://{AUTH0_DOMAIN}/authorize?response_type=code&client_id={AUTH0_CLIENT_ID}&redirect_uri={AUTH0_CALLBACK_URL}&state={STATE}

   The one we use for Mozilla is::

      https://{AUTH0_DOMAIN}/login?client={AUTH0_CLIENT_ID}&protocol=oauth2&state={STATE}&redirect_uri={AUTH0_CALLBACK_URL}&scope=openid+email+profile&response_type=code

   Look at the Auth0 and Mozilla IAM documentation for how to set up the url.

``AUTH0_CALLBACK_URL``
   str: This is the complete url to the callback view of your app that Auth0
   will redirect to after the user has authenticated.

   It needs to be something like ``https://yourdomain/auth/login``.

``AUTH0_SIGNIN_VIEW``
   str: The Django view name for the view of your signin page.

   For example, on Standup, we have a separate page for signing in and the
   Django view name is ``users.loginform``.

   This is used every time we need to logout a user and redirect them to a
   signin form.

``AUTH0_PATIENCE_TIMEOUT``
   (optional) int: The amount of time in seconds that your app will wait when
   sending requests to the Auth0 server.

   Defaults to 5.

``AUTH0_ID_TOKEN_DOMAINS``
   list of strings: The domains that require an ``id_token`` for your app.

   For Mozilla sites, this is something like:

       ``['mozilla.com', 'mozillafoundation.org', 'mozilla-japan.org']``

   If someone logs into Auth0 using an account that has a verified email address
   with one of those domains, then they'll be required to have logged in using
   an Oauth2 Auth0 provider like the Mozilla LDAP option. If they didn't use
   such a provider, they're immediately logged out and told to use an
   appropriate provider.

``AUTH0_ID_TOKEN_EXPIRY``
   (optional) int: Users who used an Oauth2 Auth0 provider and have a verified
   email address in ``AUTH0_ID_TOKEN_DOMAINS`` have their ``id_token`` renewed
   every ``AUTH0_ID_TOKEN_EXPIRY`` seconds.

   If the ``id_token`` fails renewal, the user is immediately logged out.

   Defaults to 900 (15 minutes).


Setup
=====

1. Add it to your ``settings.INSTALLED_APPS``::

      INSTALLED_APPS = [
          # blah blah blah
          'standup.auth0',
          # blah blah blah
      ]

2. Add it to your ``settings.CONTEXT_PROCESSORS``::

      CONTEXT_PROCESSORS = [
         # blah blah blah
         'standup.auth0.context_processors.auth0',
         # blah blah blah

   This step probably differs depending on how your template stuff is set up.

3. Configure the rest of the stuff. See the configuration section for details.

4. Add the signin link to your template.

   For Standup, we have a link to a sign in page in the navbar of our base template.

   Then the sign in page has this::

       {% if request.user.is_active %}
         <p>
           You are currently signed in as <b>{{ request.user.email }}</b>.
         </p>
       {% else %}
         {% if auth0configured %}
           <div class="signin-link">
             <a href="{{ auth0loginurl }}"><button class="btn login-button">Sign in to Standup</button></a>
           </div>
         {% else %}
           <p>
             Signin is not configured so it is disabled.
           </p>
         {% endif %}
       {% endif %}

   The context processor creates these vars:

   * ``auth0configured``: boolean: tells you whether auth0 is configured
   * ``auth0loginurl``: str: the login url which sends the user to the Auth0 login
     page


Flow
====

The user is happily bouncing around your site. Then the user clicks on a
``AUTH0_LOGIN_URL`` link.

::

    Browser                       Your app               Auth0 server
    |                             |                      |
    | GET AUTH0_LOGIN_URL -----------------------------> |
    | < Auth0 login page ------------------------------- |
    | ... depends on how the user logs in                |
    |                             |                      |
    | < Redirect to AUTH0_CALLBACK_URL ----------------- |
    |   has state and code                               |
    |                             |                      |
    | GET AUTH0_CALLBACK_URL ---> |                      |
    |                             | GET /oauth/token --> |
    |                             | < token_info ------- |
    |                             |   has access_token   |
    |                             |                      |
    |                             | GET /userinfo -----> |
    |                             | < user_info -------- |
    |                             |   has id_token       |
    | < Redirect to / ----------- |                      |
    |                             |                      |
    | ... time passes             |                      |
    |                             |                      |
    | GET something ------------> |                      |
    |                             | GET /delegation ---> |
    |                             | sends id_token       |
    |                             | < id_token --------- |
    | < Stuff from something ---- |                      |


This shows both the authentication flow as well as a successful renewal flow.
