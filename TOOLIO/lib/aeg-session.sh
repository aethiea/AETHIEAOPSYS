#!/usr/bin/env bash

aeg_load_session() {
    local resolver="${1:-}"
    local caller="${2:-AEG_SESSION}"
    local export_file
    local line_count
    local allowed_count
    local key
    local key_count

    unset \
        AEUSB_ROOT \
        AEXHD_ROOT \
        AEGNOSTIXXX_RESOLUTION \
        2>/dev/null || {
            echo "$caller: unable to clear inherited AEG exports" >&2
            return 1
        }

    [ -n "$resolver" ] &&
    [ -f "$resolver" ] || {
        echo "$caller: AEG resolver missing: $resolver" >&2
        return 1
    }

    export_file="$(
        mktemp "${TMPDIR:-/tmp}/aeg-session.exports.XXXXXX"
    )" || {
        echo "$caller: unable to allocate export buffer" >&2
        return 1
    }

    if ! python3 "$resolver" --exports >"$export_file"; then
        rm -f "$export_file"
        echo "$caller: fresh AEG resolution failed" >&2
        return 1
    fi

    line_count="$(
        awk '
            NF {
                count += 1
            }

            END {
                print count + 0
            }
        ' "$export_file"
    )"

    allowed_count="$(
        grep -Ec \
            '^export (AEUSB_ROOT|AEXHD_ROOT|AEGNOSTIXXX_RESOLUTION)=.+$' \
            "$export_file" ||
        true
    )"

    if [ "$line_count" -ne 3 ] ||
       [ "$allowed_count" -ne 3 ]
    then
        rm -f "$export_file"
        echo "$caller: incomplete or unexpected AEG export set" >&2
        return 1
    fi

    for key in \
        AEUSB_ROOT \
        AEXHD_ROOT \
        AEGNOSTIXXX_RESOLUTION
    do
        key_count="$(
            grep -Ec "^export ${key}=.+$" "$export_file" ||
            true
        )"

        if [ "$key_count" -ne 1 ]; then
            rm -f "$export_file"
            echo "$caller: invalid export count for $key" >&2
            return 1
        fi
    done

    # The canonical local resolver generated this file, and the content
    # has been restricted to exactly three approved export assignments.
    # shellcheck disable=SC1090
    if ! source "$export_file"; then
        rm -f "$export_file"
        echo "$caller: unable to import fresh AEG exports" >&2
        return 1
    fi

    rm -f "$export_file"

    [ "${AEGNOSTIXXX_RESOLUTION:-}" = "PASS" ] || {
        echo "$caller: AEGNOSTIXXX resolution did not pass" >&2
        return 1
    }

    [ -n "${AEUSB_ROOT:-}" ] &&
    [ -d "$AEUSB_ROOT" ] || {
        echo "$caller: resolved AEUSB root is unavailable" >&2
        return 1
    }

    [ -n "${AEXHD_ROOT:-}" ] &&
    [ -d "$AEXHD_ROOT" ] || {
        echo "$caller: resolved AEXHD root is unavailable" >&2
        return 1
    }

    return 0
}
