#!/bin/sh
# Prints Word's page and line count for a .docx (macOS + Microsoft Word).
B="$HOME/Library/Containers/com.microsoft.Word/Data/Documents"
cp "$1" "$B/ws-$$.docx"
osascript -e "
tell application \"Microsoft Word\"
  open POSIX file \"$B/ws-$$.docx\"
  set d to document \"ws-$$.docx\"
  set p to compute statistics d statistic statistic pages
  set l to compute statistics d statistic statistic lines
  set w to compute statistics d statistic statistic words
  close d saving no
  return (p as text) & \" pages, \" & (l as text) & \" lines\"
end tell"
rm -f "$B/ws-$$.docx"
rm -f "$B/~$-$$.docx"
