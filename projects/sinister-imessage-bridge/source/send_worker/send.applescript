-- send.applescript :: RKOJ-ELENO :: 2026-05-24
-- Invocation: osascript send.applescript "<service>" "<recipient>" "<body>"
-- service: "iMessage" or "SMS"
-- recipient: phone E.164 (+15551234567) or email
-- body: UTF-8 text, double-quotes escaped
on run argv
    if (count of argv) is not 3 then
        return "ERR usage: send.applescript <service> <recipient> <body>"
    end if
    set theService to item 1 of argv
    set theRecipient to item 2 of argv
    set theBody to item 3 of argv
    try
        tell application "Messages"
            set targetService to 1st account whose service type is (theService as text)
            set theBuddy to participant theRecipient of targetService
            send theBody to theBuddy
        end tell
        return "OK"
    on error errMsg number errNum
        return "ERR " & errNum & " " & errMsg
    end try
end run
