def print_d(d: dict):
    print("{\n    ", end="")

    l = len(d.items())
    for i in range(l):
        j = list(d.items())[i]

        v = str(j[1])
        vL = v.split("\n")
        vO = ""

        first = True
        for line in vL:
            if not first:
                vO += "    "
            vO += line + "\n"

            first = False

        vO = vO[:-1]

        print(f"{j[0]}: {vO}", end="")

        if i + 1 != l:
            print(",\n    ", end="")
