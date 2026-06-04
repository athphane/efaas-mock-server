**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

# **eFaas Single-Sign On Integration (Developer Portal)** 

## **Documentation Version 2.2** 

Last updated: 02[nd] November 2023 

Page **1** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Contents 

Introduction .................................................................................................................................................. 4 Terminology .............................................................................................................................................. 4 Getting Started .............................................................................................................................................. 5 Important URLs ......................................................................................................................................... 5 Client Creation .......................................................................................................................................... 5 eFaas Scopes ................................................................................................................................................. 6 Sample User Claims ....................................................................................................................................... 7 eFaas Integration Overview ........................................................................................................................ 10 Authorization Flows .................................................................................................................................... 11 Introduction ............................................................................................................................................ 11 Hybrid Flow ............................................................................................................................................. 11 Authorization Code Flow + PKCE ............................................................................................................ 11 Overall Authorization Flow ......................................................................................................................... 12 IMPORTANT ................................................................................................................................................ 13 Sample Requests For Hybrid Flow .............................................................................................................. 14 Authentication Request .......................................................................................................................... 14 A note about state parameter ................................................................................................................ 15 Token Request ........................................................................................................................................ 16 Sample Requests For Authorization Code + PKCE ...................................................................................... 17 Authentication Request .......................................................................................................................... 17 Token Request ........................................................................................................................................ 18 Token Validation ......................................................................................................................................... 19 Retrieving User Info .................................................................................................................................... 20 Retrieving User Photo ................................................................................................................................. 20 Tracking changes to User Information ........................................................................................................ 20 Refreshing Tokens ....................................................................................................................................... 21 Introduction ............................................................................................................................................ 21 Prerequisite ............................................................................................................................................. 21 Refresh Token Request ........................................................................................................................... 21 Logging User Out ......................................................................................................................................... 22 Sample Request ...................................................................................................................................... 22 

Page **2** of **30** 

## **National Centre for Information Technology** 

## 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

Common Mistakes .................................................................................................................................. 22 Single Sign Out ............................................................................................................................................ 23 Introduction ............................................................................................................................................ 23 Prerequisite (For Server Side Applications Only) .................................................................................... 23 Back channel logout ................................................................................................................................ 23 Front channel logout ............................................................................................................................... 23 Browser-Based JavaScript Clients ........................................................................................................... 24 eFaas One-Tap Login - Third Party Apps Integration .................................................................................. 25 Introduction ............................................................................................................................................ 25 Overall Flow ............................................................................................................................................ 26 OneTap Login -  Third Party Apps Integration............................................................................................. 27 Pre-requisite............................................................................................................................................ 27 Implementation Steps ............................................................................................................................. 27 TROUBLESHOOTING COMMON ERRORS .................................................................................................... 28 BEFORE DEPLOYING TO PRODUCTION........................................................................................................ 29 FURTHER READING ..................................................................................................................................... 30 

Page **3** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Introduction 

eFaas is an openid connect single sign-on which provides a secure authentication process and a consent based mechanism to share the user data. 

This document is intended to guide you through the process of eFaas integration. 

## Terminology 

|Terminology||
|---|---|
|Relying Party (Client)|Application trying to authenticate the user|
|User|Anyone who is using eFaas to authenticate themselves to other<br>applications|
|JWT(JSON Web Token)|A self-contained and digitally signed JSON string that contains<br>information about the authentication event and user.|
|access_token|JWT that is used to grant access to protected resources|
|id_token|JWT that contains information about authentication event and can<br>optionally contain user information|
|Code|Authorization code that can be exchanged for an id_token and<br>access_token and/or refresh token|
|Discovery Document|The end point that returns urls and information associated with eFaas|
|Server side client|Relying parties that can keep a client secret confidentially and will<br>maintain a session of their own after authorization (eg: MVC<br>applications that use cookies to maintain session)|
|Non Server side client|Relying parties that cannot store a client secret confidentially and will<br>depend entirely on eFaas for maintaining session (eg: Single page<br>Application)|



Page **4** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Getting Started 

## Important URLs 

|Important URLs||
|---|---|
|Developer Base<br>URL|https://developer.gov.mv/efaas|
|Production Base<br>URL|https://efaas.gov.mv|
|Discovery<br>Document Url|`{efaas_base_url}/.well-known/openid-configuration`|



## Client Creation 

When submitting client creation form, make sure you have provided the following information: 

- Correct grant type 

- Redirect URIs 

- Post logout URI 

- Backchannel or front channel logout URI (For server side applications only) 

- Scopes required by your application 

- If you require to refresh tokens 

After submitting the client creation form, you will receive client credentials for both development and production environment. A client credential consists of: 

|Client Id|A unique identifier issued to the consumer to identify itself to eFaas|
|---|---|
|Client Secret|A shared secret established between the eFaas and consumer|



Page **5** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## eFaas Scopes 

eFaas scopes are used to indicate what user information (user claims) will be made available from eFaas to the Relying Party (Client). 

Relying Parties should only request the minimum number of scopes that would fulfil their application’s requirements. 

The following is a list of available scopes in efaas 

**NOTE** : **openid** and **efaas.profile** will be assigned to all clients by default. Also the legacy **profile** scope will continue to work until we migrate all the current efaas clients to use the new scopes. 

- openid 

- efaas.profile 

- efaas.email 

- efaas.mobile 

- efaas.birthdate 

- efaas.photo 

- efaas.work_permit_status 

- efaas.passport_number 

- efaas.country 

- efaas.permanent_address 

Page **6** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Sample User Claims 

The following tables show details of claims associated with each eFaas scope. 

**Scope** : efaas.openid 

|**Scope**: efaas.openid||||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|sub|Unique user key assigned to the<br>user|string|178dedf2-581b-4b48-<br>9d73-770f302751dc|



**Scope** : efaas.profile 

|**Scope**: efaas.profile||||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|first_name|First name of the user|string|Mariyam|
|middle_name|Middle name of the user|string|Ahmed|
|last_name|Last name of the user|string|Rasheed|
|first_name_dhivehi|First name of the user in Dhivehi<br>(Maldivians only)|string|_މރޔމ_|
|middle_name_dhivehi|Middle name of the user in<br>Dhivehi(Maldivians only)|string|_އހމދ_|
|last_name_dhivehi|Last name of the user in dhivehi<br>(Maldivians only)|string|_ރޝދ_|
|gender|Gender of the user|string|M/F|
|idnumber|Identification number of the<br>user<br>•<br>National ID number for<br>Maldivians<br>•<br>Work permit number for<br>work permit holders<br>•<br>Passport number for<br>other foreigners|string|A000111 / WP941123 /<br>LA110011|
|verified|Indicates if the user is verified|boolean|True/False|
|verification_type|Type of verification taken by the<br>user|string|biometric / in-person|
|last_verified_date|The last date when the user was<br>verified either using biometrics<br>or by visiting an eFaas<br>verification counter|date<br>(M/dd/yyyy<br>h:mm:ss tt)|6/26/2019 9:18:11 AM|
|user_type_description|Indicates the type of user|string|•<br>Maldivian<br>•<br>Work Permit<br>Holder<br>•<br>Foreigner|
|updated_at|The last date when the user<br>information was updated|date<br>(M/dd/yyyy<br>h:mm:ss tt)|6/15/2023 2:12:38 PM|



Page **7** of **30** 

64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## **National Centre for Information Technology** 

**Scope** : efaas.email 

|**Scope**: efaas.email||||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|email|Email of the user|string|ahmed_ali@gmail.com|



**Scope** : efaas.mobile 

|**Claim name**|**Description**|**Type **|**Example**|
|---|---|---|---|
|mobile|Mobile number of the user|string|9074512|
|country_dialing_code|Dialing code of the registered<br>number|string|+960|



**Scope** : efaas.birthdate 

|**Scope**: efaas.birthdate||||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|birthdate|Date of birth of the user|date<br>M/dd/yyyy|12/20/1990|



**Scope** : efaas.photo 

|**Scope**: efaas.photo||||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|photo|Photo of the user|url|https://efaas-api<br>egov.mv/user/photo|



**Scope** : efaas.work_permit_status 

|**Scope**: efaas.work_permit|_status|||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|is_workpermit_active|Boolean indicating if the work<br>permit is active (only applicable<br>to workpermit holders)|boolean|boolean|



**Scope** : efaas.passport_number 

|**Scope**: efaas.passport_nu|mber|||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|passport|Passport number of the user|string|12/20/1990|



**Scope** : efaas.country 

|**Claim name**|**Description**|**Type **|**Example**|
|---|---|---|---|
|country_name|Name of the countryof the user|string|Maldives|
|country_code|ISO 3-digit code|int|462|
|country_code_alpha3|ISO alpha3 code|string|MDV|
|country_dialing_code|Dialingcode of the country|string|+960|



Page **8** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

**Scope** : efaas.permanent_address 

|**Scope**: efaas.permanent_|address|||
|---|---|---|---|
|**Claim name**|**Description**|**Type **|**Example**|
|permanent_address|Permanent address of the user|String (JSON)|Given below|



**Note** : JSON string escaping has been removed for readability 

{ 

"AddressLine1": "Blue Light", "AddressLine2": "", "Road": "Road Name", "AtollAbbreviation": "K", 

"AtollAbbreviationDhivehi": " _ކ_ ", 

"IslandName": "Male'", 

"IslandNameDhivehi": " _ެމާލ_ ", 

"HomeNameDhivehi": " _ްބްލޫ ލައިޓ_ ", "Ward": "Maafannu", "WardAbbreviationEnglish": "M", 

"WardAbbreviationDhivehi": " _މ_ ", "Country": "Maldives", "CountryISOThreeDigitCode": "462", "CountryISOThreeLetterCode": "MDV" } 

Page **9** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## eFaas Integration Overview 

The following functionalities should be implemented for a successful eFaas integration: 

1. Authentication request 

2. Token request 

3. Validating tokens 

4. Retrieving user info from userinfo endpoint 

5. Refreshing tokens if required 

6. Logging the user out 

7. Single sign-out 

8. eFaas One-Tap Login 

Page **10** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Authorization Flows 

## Introduction 

An authorization flow or a grant type describes the process by which a client obtains tokens from the authorization server(eFaas). 

Currently we support two types of authorization flows in eFaas. They are: 

- Hybrid (For server-side applications) 

- Authorization Code + PKCE (For non-server side applications. eg: SPAs and mobile applications) 

## Hybrid Flow 

Hybrid flow is used by server-side applications that can keep a secret confidentially and maintain their own session. 

## Authorization Code Flow + PKCE 

This flow is mainly used by browser based applications like SPAs and mobile applications that cannot keep a secret confidentially. However, Authorization Code + PKCE can be used by server side applications as well. 

Previously **implicit flow** was used for non-server side applications, however OAuth 2.0 Best Practices now **recommend against** using this flow due to many risks such as returning access token in the URL. 

Page **11** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Overall Authorization Flow 

The authorization steps for both hybrid and authorization code + PKCE are same with only differences in parameters for authentication request and token requests. We will look at these requests in more detail in the next section. 

Page **12** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## IMPORTANT 

In the following sections we have described how to manually create authentication requests and exchange authorization codes for tokens. However, **we strongly recommend** using openid connect or OAuth libraries developed for the respective frameworks. These libraries provide extension methods for logging in and logging out the users. They also handle PKCE challenges, token exchanges, generation and validation of state and nonce parameters and load user info as well. 

Page **13** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Sample Requests For Hybrid Flow 

## Authentication Request 

**URL** : {efaas_base_url}/connect/authorize 

## **Method** : GET 

|**Method**: GET||
|---|---|
|QueryParameters|Description|
|client_id|The client idprovided duringclient registration|
|redirect_uri|The URI that is registered at eFaas as a callback uri|
|response_type|Space delimited values to indicate what to receive from eFaas as a reponse.<br>For hybrid this should be one of<br>•<br>code id_token<br>•<br>code token<br>•<br>code id_token token|
|scope|The scopes that the relying party requires from eFaas. The values should be<br>space delimited.<br>**eg**: openid efaas.profile|
|nonce|A value that uniquely identifies the authorization request. It will be returned<br>in the id_token.|
|state|This is a randomly generated string to prevent CSRF attacks and maintain state<br>between eFaas and RP. The value of state parameter will be returned by eFaas<br>duringcallback.|



## **Sample Authentication Request** 

```
https://developer.gov.mv/efaas/connect/authorize?client_id=def7fc52-0761-4916-82e5-
9b759d2f3589&redirect_uri=https://myapp.gov.mv/signin-oidc&response_type=code
id_token&scope=openid profile&response_mode=form_post&nonce=nonce_123&state=state_abc
```

## **Note** : URL encoding is removed for readability 

Page **14** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## A note about state parameter 

Please do not send static values in the state parameter. 

For example ……&state=adminLogin 

State parameter must always be a random, unique and non-guessable. It should also be validated on eFaas callback to prevent CSRF attacks. 

If your application requires additional context data to be maintained between authentication request and eFaas callback, you can store the information in session or the local storage of the browser with state parameter as the key. You may refer to this link for the implementation details - - https://auth0.com/docs/secure/attack protection/state parameters 

Page **15** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Token Request 

When you receive the callback after a successful authorization request, you can exchange the code for an access token and in some cases a refresh token using the token endpoint 

## **Method:** POST 

## **URL:** {efaas_base_url}/connect/token 

## **Content-Type:** application/x-www-form-urlencoded 

|**Params**|**Description**|
|---|---|
|client_id|The client idprovided duringclient registration|
|client_secret|The client secretprovided duringclient registration|
|grant_type|Thegrant type in this case is authorization_code|
|code|The authorization code received from eFaas|
|redirect_uri|The URI that is registered at eFaas as a callback uri|
|||



## **Sample Token Request** 

```
client_id=abc44ec3-aa7b-4eab-a50e-4d18f17c3f62&client_secret=9fz11cd8-7bb8-40fa-b3eb-
bc5dc43439c3&grant_type=authorization_code&code=12b2478a5b71d175de8c50327fc33491bb0b51
9491608627c1cf0be46fb3610d&redirect_uri=https://myapp.gov.mv/signin-oidc
```

Page **16** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Sample Requests For Authorization Code + PKCE 

This flow introduces additional parameters called code_verifier, code_challenge and code_challenge_method. 

A code_verifier is a cryptographically random string that is generated and stored by the Relying Party. The code_challenge is the base64 encoded and SHA256 hashed value of the code_verifier. 

The code_challenge is sent in the authentication request to the eFaas and eFaas will store this value. The code_verifier is sent to eFaas in the token request which will validated by eFaas. The token will only be issued if the hash of the code_verifier matches with the code_challenge. 

## Authentication Request 

**URL** : {efaas_base_url}/connect/authorize 

## **Method** : GET 

|**Method**: GET||
|---|---|
|QueryParameters|Description|
|client_id|The client idprovided duringclient registration|
|redirect_uri|The URI that is registered at eFaas as a callback uri|
|response_type|Space delimited values to indicate what to receive from eFaas as a reponse.<br>For authorization code + PKCE it should be code.|
|scope|The scopes that the relying party requires from efaas. The values should be<br>space delimited.<br>eg: openid efaas.profile|
|code_challenge|This is the base64 encoded SHA256 hash of the code verifier|
|code_challenge_method|Method used to hash the code_verifier(SHA256)|
|state|This is a randomly generated string to prevent CSRF attacks and maintain<br>state between eFaas and RP. The value of state parameter will be returned<br>byeFaas duringcallback.|



## **Sample Authentication Request** 

```
https://developer.gov.mv/efaas/connect/authorize?response_type=code&client_id=dc8311c9
-6c42-449e-a080-0d031d2612ab&state=abc&scope=openid efaas.profile&redirect_uri=
```

```
https://myapp.gov.mv/signin-oidc&code_challenge=K29soCkThVHYUT-
```

```
r4uZtRMdTKb584oZLh83rd8MGqJk&code_challenge_method=S256
```

Page **17** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Token Request 

When you receive the callback after a successful authorization request, you can exchange the code for an access token and, in some cases a refresh token, using the token endpoint. 

For Authorization Code + PKCE, code_verifier must be included in the token request. 

## **Method:** POST 

## **URL:** {efaas_base_url}/connect/token 

## **Content-Type:** application/x-www-form-urlencoded 

|**Params**|**Description**|
|---|---|
|client_id|The client idprovided duringclient registration|
|client_secret|The client secret provided during client registration. Client secret is**not required**for<br>non-server side applications.|
|grant_type|Thegrant type in this case is authorization_code|
|code|The authorization code received from eFaas|
|redirect_uri|The URI that is registered at efaas as a callback uri|
|code_verifier|The unhashed code_challenge|



## **Sample Token Request** 

```
client_id=abc44ec3-aa7b-4eab-a50e-4d18f17c3f62
&grant_type=authorization_code&code=12b2478a5b71d175de8c50327fc33491bb0b519491608627c1
cf0be46fb3610d&redirect_uri=https://myapp.gov.mv/signin-
oidc&code_verifier=eImN_fPyl2gbkUVrSVTrenoJYAIhTS3M-aaQ3Lx45Kbs
```

Page **18** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Token Validation 

The Relying Party must validate the JWTs received from eFaas (id_token, access_token). 

We strongly recommend using middleware provided by your application’s framework or third-party libraries for validating tokens. You can find a list of libraries for common programming frameworks at the following link: 

https://jwt.io/libraries 

For further information, please refer to OpenId Specification at: 

https://openid.net/specs/openid-connect-core-1_0.html 

Page **19** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Retrieving User Info 

Although user info is available in the id_token, it is recommended to use the userinfo endpoint provided by eFaas to retrieve the user info. Most of the openid connect libraries will do this automatically for you. 

## Method: GET 

## **URL:** {efaas_base_url}/connect/userinfo 

|Params|Description|
|---|---|
|Header:<br>Authorization|Include the access token received after authentication|



## Retrieving User Photo 

Applicable only if the client has **efaas.photo** scope. 

## Method: GET 

## **URL:** {photo_url_from_user_info_json} 

|Params|Description|
|---|---|
|Header:<br>Authorization|Include the access token received after authentication|



## Tracking changes to User Information 

Client applications are expected to keep a track of the **updated_at** user claim and update the user information accordingly. 

Page **20** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Refreshing Tokens 

## Introduction 

If you are accessing a RESTful API secured by eFaas, then you will require to refresh the access tokens, as access tokens expire quickly. This can be done by using the refresh_token received during the initial token request. When the refresh token request is successful, you will receive a new access_token and a new refresh_token. 

## Prerequisite 

To be able to use refresh tokens, the Relying Party must be assigned offline_access scope during client registration. The Relying Party also needs to include offline_access scope in the authentication request. 

## Refresh Token Request 

## **Method:** POST 

## **URL:** {efaas_base_url}/connect/token 

**Content-Type:** application/x-www-form-urlencoded 

|**Params**|**Description**|
|---|---|
|client_id|The client idprovided duringclient registration|
|client_secret|The client secret provided during client registration. Client secret is**not**<br>**required**for non-server side applications.|
|grant_type|Thegrant type in this case is refresh_token|
|refresh_token|The refresh_token received from initial token request|



## **Sample Token Request** 

```
client_id=abc44ec3-aa7b-4eab-a50e-4d18f17c3f62&client_secret=9fz11cd8-7bb8-40fa-b3eb-
bc5dc43439c3&grant_type=refresh_token&refresh_token=EFC5388CF55A8368DC0B69ECB82E4250F3
359FD0F3EA23E52A4E502808A5AAS
```

Page **21** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Logging User Out 

To log the user out of eFaas, send a GET request to endsession endpoint of eFaas with parameters in the table below. 

After a successful logout, the user will be redirected to the registered post_logout_redirect_uri. 

## **Method** : GET 

## **URL:** {efaas_base_url}/connect/endsession 

|**URL:**{efaas_base_url}/connec|t/endsession|
|---|---|
|Params|Description|
|post_logout_redirect_uri|Thepost logout redirect uri that was registered at efaas|
|Id_token_hint|The id_token received duringthe authorizationprocess|
|state|This is for round tripping state between the relying party and<br>efaas|



## Sample Request 

```
https://developer.gov.mv/efaas/connect/endsession?post_logout_redirect_uri=ht
tps://efaasapp.gov.mv/oidc/signout&id_token_hint=eyJhbGciOiJSUzI1NiIsImtpZCI6
Ijc5M0E3NjB.eyJuYmYiOjE2MTQ1MDA2MTAsImV4cCI6MTYxNDUwMDkx&state=state_abc
```

## Common Mistakes 

- Providing access_token instead of id_token to the endsession endpoint. 

- Incorrect post_logout_redirect_uri 

The post_logout_redirect_uri must exactly match with the one configured for the client. No query parameters should be passed to the post_logout_redirect_uri. 

For example, if the post_logout_redirect_uri is https://efaasapp.gov.mv/oidc/signout, only https://efaasapp.gov.mv/oidc/signout will be considered valid. 

The following URLs will be considered **INVALID** : 

- https://efaasapp.gov.mv/oidc/signout/ 

- https://efaasapp.gov.mv/oidc/signout?param=one 

Page **22** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Single Sign Out 

## Introduction 

A single sign-out is used to log out the user from all applications that’s sharing the same eFaas session, if that session is terminated either by log out from one of the applications or log out from eFaas directly. 

For server side applications, this is accomplished using back channel and front channel logout. 

## Prerequisite (For Server Side Applications Only) 

Relying parties must register a back_channel_logout_uri or front_channel_logout_uri depending on how they plan to implement this type of logout. The relying party must also store the eFaas session id when persisting the user session 

## Back channel logout 

A POST request will be sent from the eFaas server to the relying party’s registered back_channel_logout_uri. 

**URL** : { back_channel_logout_uri } 

**Method** : POST 

**Content-Type:** application/x-www-form-urlencoded 

**Content** : logout_token= `eyJhbGciOiJSUzI1NiM0E3NjB.eyJuYmYiOj` 

The relying party should validate the logout_token and retrieve the eFaas session id (sid) in the token. Remove the user session if sid matches with the sid in the user’s session. Once the session is removed, the relying party must respond to eFaas with a 200 OK response. 

## Front channel logout 

A GET request will be sent from the user’s browser to the relying party’s registered front_channel_logout_uri. 

**URL** { front_channel_logout_uri } 

## **Method** : GET 

**Query Parameter** : logout_token= `eyJhbGciOiJSUzI1NiM0E3NjB.eyJuYmYiOj` 

The relying party should validate the logout_token and retrieve the eFaas session id (sid) in the token. Remove the user session if sid matches with the sid in the user’s session. 

Page **23** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Browser-Based JavaScript Clients 

To handle single sign-out, these applications must implement monitoring for check_session_iframe endpoint of eFaas. You can refer to the specifications at https://openid.net/specs/openid-connectsession-1_0.html for implementing this feature. 

If you’re are using **oidc-client-js** library (https://github.com/IdentityModel/oidc-client-js ) this will be already implemented for you. 

Page **24** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## - - eFaas One Tap Login Third Party Apps Integration 

## Introduction 

eFaas one-tap login allows users to log into third-party applications through eFaas Mobile Application, without having to re-enter their credentials. 

The following is a screenshot of eFaas Mobile Application, with a list of eFaas integrated services displayed to the user. When a user clicks one of the service icons, they will be logged into the service application without having to re-enter their eFaas credentials. 

Page **25** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## Overall Flow 

The following diagram shows the eFaas One-Tap login flow with Gov.Mv as the third-party application. 

Page **26** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## - OneTap Login Third Party Apps Integration 

## Pre-requisite 

All third-party applications **must implement** the following endpoint which will be called by the eFaas Mobile Application for one-tap logins. 

- **Endpoint** : {root_url}/efaas-one-tap-login 

- **HTTP Method** : GET 

## Implementation Steps 

1. eFaas Mobile application calls the one-tap endpoint of the third-party application with 

`efaas_login_code` included as a query parameter (eg: https://gov.mv/efaas-one-taplogin?efaas_login_code=a5d9a8ac-d583-41a7-8844-545dd608fad7) 

2. The third-party application extracts the `efaas_login_code` from the endpoint. 

3. Add the `efaas_login_code` to the `acr_values` parameter of efaas authorization url before redirecting to efaas for authentication 

{ 

client_id: CLIENT_ID, 

redirect_uri: REDIRECT_URL, 

response_type: RESPONSE_TYPE, 

scope: "openid profile", 

acr_values: "efaas_login_code:a5d9a8ac-d583-41a7-8844-545dd608fad7" 

} 

4. eFaas authenticates the user by validating the `efaas_login_code` and redirects to third-party application's callback url. The standard OAuth flow will continue from here. 

Page **27** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## TROUBLESHOOTING COMMON ERRORS 

- After logout the user is not redirected back to the application 

   - Check if the PostLogoutURL is correct 

   - Check if the value passed to id_token_hint is the id_token and NOT access token 

- 419 Page Expired error when redirecting to the application 

   - Exclude the redirect URL from CSRF protection. For Laravel applications refer to this link https://laravel.com/docs/10.x/csrf#csrf-excluding-uris 

Page **28** of **30** 

**National Centre for Information Technology** 64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## BEFORE DEPLOYING TO PRODUCTION 

- Make sure the following requests are working 

   - Authorization request 

   - Token request 

   - Refresh token request 

   - Logout 

   - Post logout redirection 

   - Backchannel or front channel logout 

- Inform the production server IPs to be whitelisted, if hosting on a cloud based service. 

Page **29** of **30** 

**National Centre for Information Technology** 

64, Kalaafaanu Hingun, Male’ City, Republic of Maldives 

## FURTHER READING 

- OAuth 2.0 RFC 

`o` https://datatracker.ietf.org/doc/html/rfc6749 

- OpenID Connect Specifications 

`o` https://openid.net/specs/openid-connect-core-1_0.html 

- OAuth 2.0 Threat Model and Security Considerations 

`o` https://datatracker.ietf.org/doc/html/rfc6819 

- OAuth 2.0 Security Best Current Practice 

`o` https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics 

## **END OF DOCUMENTATION** 

Page **30** of **30** 

