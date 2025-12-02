#!/usr/bin/env bash

# ArvanCloud DNS API - Final version
# Requires: export Arvan_Token="your_api_token"
# Optional: export ARVAN_CDN_API=1

ARVAN_API="https://napi.arvancloud.ir"

dns_arvan_add() {
  fulldomain=$1
  txtvalue=$2

  _debug fulldomain "$fulldomain"
  _debug txtvalue "$txtvalue"

  if [ -z "$Arvan_Token" ]; then
    _err "You must export variable: Arvan_Token"
    return 1
  fi

  if ! _get_root "$fulldomain"; then
    return 1
  fi

  _debug "Adding TXT record to $_sub_domain in $_domain"

  _api_url="$ARVAN_API/cdn/4.0/domains/$_domain/dns-records"

  _data="{\"name\":\"$_sub_domain\",\"value\":{\"text\":\"$txtvalue\"},\"type\":\"txt\",\"ttl\":120,\"cloud\":false,\"upstream_https\":\"default\",\"ip_filter_mode\":{\"count\":\"single\",\"order\":\"none\",\"geo_filter\":\"none\"}}"

  export _H1="Authorization: apikey $Arvan_Token"
  export _H2="Content-Type: application/json"
  export _H3="User-Agent: acme.sh"

  _response="$(_post "$_data" "$_api_url" "" "POST")"
  _debug2 _response "$_response"

  if echo "$_response" | grep -q '"errors"'; then
    _err "Error from Arvan API: $_response"
    return 1
  fi

  return 0
}

dns_arvan_rm() {
  fulldomain=$1
  txtvalue=$2

  _debug fulldomain "$fulldomain"
  _debug txtvalue "$txtvalue"

  if [ -z "$Arvan_Token" ]; then
    _err "You must export variable: Arvan_Token"
    return 1
  fi

  if ! _get_root "$fulldomain"; then
    return 1
  fi

  _api_url="$ARVAN_API/cdn/4.0/domains/$_domain/dns-records"

  export _H1="Authorization: apikey $Arvan_Token"
  export _H2="Content-Type: application/json"
  export _H3="User-Agent: acme.sh"

  _response="$(_get "$_api_url")"
  _debug2 _response "$_response"

  record_id="$(echo "$_response" | grep -oE '"id":"[^"]+"' | head -n 1 | cut -d : -f 2 | tr -d \")"

  if [ "$record_id" ]; then
    _api_url="$ARVAN_API/cdn/4.0/domains/$_domain/dns-records/$record_id"
    _debug "Deleting record ID: $record_id"
    _response="$(_get "$_api_url" "" "DELETE")"
    _debug2 _response "$_response"
  else
    _info "No record found to delete"
  fi

  return 0
}

_get_root() {
  domain=$1
  i=1
  while true; do
    h=$(echo "$domain" | cut -d . -f $i-100)
    if [ -z "$h" ]; then
      return 1
    fi

    export _H1="Authorization: apikey $Arvan_Token"
    export _H2="Content-Type: application/json"
    export _H3="User-Agent: acme.sh"

    response="$(_get "$ARVAN_API/cdn/4.0/domains/$h")"
    _debug2 response "$response"

    if echo "$response" | grep "\"name\":\"$h\"" >/dev/null; then
      _sub_domain="$(echo "$domain" | sed "s/\\.$h\$//")"
      _domain=$h
      return 0
    fi
    i=$(_math "$i" + 1)
  done
  return 1
}
