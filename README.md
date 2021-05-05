# UpCheck
Check status of websites. Send notification if down.

## Key features in this version:
- Allows simple mode (provide a single URL as the only parameter)
- Supports Alert IDs -- whenever a site is unreachable, a random tracking ID is generated and referenced with each subsequent check. If the site becomes reachable, an 'All-clear' message is sent (and you can go back to bed)

- Note that this requires the following configuration files to run:

## sites.json - specify sites to check
- note that the port array is optional. If not specified, will include default ports 80 & 443
```
[
    {
        "name":"invalid",
        "url":"wwww.googel.com"
    },
    {
        "name":"google",
        "url":"www.google.com",
        "ports":["443","80"]
    }
]
```

## env.json - a valid smtp email login
- I'd recommend an internal email server or else GMX
```
{
    "SMTPserver" : "mail.gmx.com",
    "sender" :     "youremail@gmx.com",
    "USERNAME" : "username",
    "PASSWORD" : "password"
}
```

## dl.json - distribution list
- Needs to contain names and emails.
```
[
    {
        "name":"steve1",
        "email":"steve@domain.com"
    },
    {
        "name":"steve2",
        "email":"steve2@domain.com"
    } 
]
```
