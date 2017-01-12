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

See ``standup.auth0.settings``.


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
