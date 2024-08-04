from pypdf import PdfWriter, PdfReader
from pypdf.annotations import Rectangle

writer = PdfWriter()  # open output
reader = PdfReader("/Users/cussa/Downloads/Troika! Community Content.pdf")  # open input

key = "/Annots"
uri = "/URI"
ank = "/A"

internal = "https://internal/"
group = "https://group/"

bookmarkParent = None
bookmarkRoot = writer.add_outline_item("Troika! Community Content", 0)

colours = {"Bestiary": "#FCDAEE", "Bacgrounds": "#FCF9DA"}

currentColor = None

# writer.addPage(reader.getPage(0))  # insert page
for p in reader.pages:
    # if p.page_number != 3:
    #     continue
    bookmarked = False

    if not p.annotations:
        writer.add_page(p)
        continue
    to_remove = []
    for annotation in p.annotations:
        if ank not in annotation.keys():
            continue

        link = annotation[ank][uri]
        if not link.startswith(internal) and not link.startswith(group):
            continue

        if not bookmarked:
            bookmarkName = (
                link.replace(group, "").replace(internal, "").replace("%C2%A7", " ")
            )
            # print(bookmarkName)
            bookmarkParent = bookmarkRoot if group in link else bookmarkParent
            bookmark = writer.add_outline_item(
                bookmarkName, p.page_number, bookmarkParent
            )
            if group in link:
                bookmarkParent = bookmark
                currentColor = colours[bookmarkName]
            bookmarked = True
        to_remove.append(annotation)
    for rem in to_remove:
        p.annotations.remove(rem)

    # if currentColor:
    #     p.draw_rect(p.rect, color=None, fill=currentColor, overlay=False)

    writer.add_page(p)

# first = True
# depth = -1


# def write_outline(outline):
#     global first, depth
#     for o in outline:
#         if first:
#             first = False
#             continue
#         if type(o) == list:
#             depth += 1
#             write_outline(o)
#             depth -= 1
#         else:
#             title = o["/Title"]
#             page = o["/Page"]
#             space = "\t" * depth
#             print(f"{space}{title} - {page}")


# write_outline(writer.outline)

writer.page_mode = "/UseOutlines"
with open("Troika Community Content.pdf", "wb") as fp:  # creating result pdf JCT
    writer.write(fp)  # writing to result pdf JCT
