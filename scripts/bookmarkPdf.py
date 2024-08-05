from pypdf import PdfWriter, PdfReader
from pypdf.annotations import Link
from pypdf.generic import Fit

writer = PdfWriter()  # open output
reader = PdfReader("Troika! Community Content_source.pdf")  # open input
cover = PdfReader("cover.pdf")

writer.append(cover)

key = "/Annots"
uri = "/URI"
ank = "/A"

internal = "https://internal/"
group = "https://group/"
index = "https://index/"

bookmarkParent = None
bookmarkParentName = None
bookmarkRoot = writer.add_outline_item("Troika! Community Content", 0)

toc = {"Bestiary": {}, "Backgrounds": {}}

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
    to_add = []
    for annotation in p.annotations:
        if ank not in annotation.keys():
            continue

        link = annotation[ank][uri]
        if link.startswith(index):
            cleanLink = link.replace(index, "").replace("%C2%A7", " ").split("%C2%B1")
            parent = cleanLink[0]
            destination = cleanLink[1]
            destinationPage = toc[parent][destination]
            originalRect = annotation.get_object()["/Rect"]
            index_annotation = Link(
                rect=originalRect,
                target_page_index=destinationPage,
                # fit=Fit(fit_type="/XYZ", fit_args=(123, 0, 0)),
            )
            to_add.append(index_annotation)
            to_remove.append(annotation)
            continue

        if not link.startswith(internal) and not link.startswith(group):
            continue

        if not bookmarked:
            bookmarkName = (
                link.replace(group, "").replace(internal, "").replace("%C2%A7", " ")
            )
            # print(bookmarkName)
            bookmarkParent = bookmarkRoot if group in link else bookmarkParent
            bookmarkParentName = bookmarkName if group in link else bookmarkParentName
            bookmark = writer.add_outline_item(
                bookmarkName, p.page_number + 1, bookmarkParent
            )
            if group in link:
                bookmarkParent = bookmark
                currentColor = colours[bookmarkName]
            else:
                toc[bookmarkParentName][bookmarkName] = p.page_number + 1
            bookmarked = True
        to_remove.append(annotation)
    for rem in to_remove:
        p.annotations.remove(rem)

    # if currentColor:
    #     p.draw_rect(p.rect, color=None, fill=currentColor, overlay=False)

    writer.add_page(p)

    for add in to_add:
        writer.add_annotation(page_number=p.page_number + 1, annotation=add)


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
with open("Troika! Community Content.pdf", "wb") as fp:  # creating result pdf JCT
    writer.write(fp)  # writing to result pdf JCT
