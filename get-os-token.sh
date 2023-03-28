# utility for getting object store token.
# assumes that youve set OS_CREDS which points to a json formatted file containing the objectstore credentials. See README for specifics.
curl -H "Content-Type: application/json" -s 'https://identity.stack.cloudvps.com/v2.0/tokens' -d @$OS_CREDS | python -c "import sys; import json; print(json.loads(sys.stdin.read())['access']['token']['id'])"
