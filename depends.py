#!/usr/bin/env python3
import fileinput

print("""<!DOCTYPE HTML>
<html>
<meta charset="UTF-8">
<head>
<link rel="stylesheet" type="text/css" href="gstyle.css">
<title>Package information page for """)

def _list(depends):
    depends = depends.replace("|","<em>[OR]</em>").split(", ")
    print('<ul class="pkglist">')
    for i in depends:
        if not i.startswith("${"):
            print("<li>{}</li>".format(i))
    print("</ul>")

fields = ("Build-Depends:","Depends:","Recommends:",
        "Suggests:","Enhances:","Provides:","Conflicts:","Breaks:",
        "Replaces:","Pre-Depends:","Build-Depends-Indep:",
        "Build-Conflicts:", "Build-Conflicts-Indep:", "Built-Using:")
for line in fileinput.input():
    line = line.split(" ",1)
    if fileinput.isfirstline():
        print("""{a}</title>
        </head>
        <body>
        <h2>Source package {a}</h2>""".format(a=line[1]))
    elif line[0] in fields:
        print("<h3>{}</h3>".format(line[0]))
        _list(line[1])
    elif line[0] == "Package:":
        print("<h2>Binary package {}</h2>".format(line[1]))

print("""
</body>
</html>""")
