# import libraries
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
endpoint = "https://mbue-doc-ai-test.cognitiveservices.azure.com/"
key = "369b59721efd4d8eaf87436788dd64ec"


def format_bounding_region(bounding_regions):
    if not bounding_regions:
        return "N/A"
    return ", ".join(
        "Page #{}: {}".format(region.page_number, format_polygon(region.polygon))
        for region in bounding_regions
    )


def format_polygon(polygon):
    if not polygon:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in polygon])


def analyze_general_documents():
    # sample document
    # docUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"
    # docUrl = "https://raw.githubusercontent.com/rcgreen99/ms-doc-ai/88ef4ba4be08f8586c2166ab42c5766c1bd36b3f/data/original.pdf"
    # docUrl = "https://raw.githubusercontent.com/rcgreen99/ms-doc-ai/5fcdc420d02d7d4374a74320860cfc57464500cd/data/compressed_original.pdf"
    docUrl = "https://raw.githubusercontent.com/rcgreen99/ms-doc-ai/1637d85d97771c8abe698dd598112617e303dc24/data/revised.pdf"
    # docUrl = "https://raw.githubusercontent.com/rcgreen99/ms-doc-ai/1c77041f91fbaee4cc2793ba4e7a5e513650748a/data/00031_original.pdf"

    # create your `DocumentAnalysisClient` instance and `AzureKeyCredential` variable
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_analysis_client.begin_analyze_document_from_url(
        "prebuilt-document", docUrl
    )
    result = poller.result()

    for style in result.styles:
        if style.is_handwritten:
            print("Document contains handwritten content: ")
            print(
                ",".join(
                    [
                        result.content[span.offset : span.offset + span.length]
                        for span in style.spans
                    ]
                )
            )

    print("----Key-value pairs found in document----")
    for kv_pair in result.key_value_pairs:
        if kv_pair.key:
            print(
                "Key '{}' found within '{}' bounding regions".format(
                    kv_pair.key.content,
                    format_bounding_region(kv_pair.key.bounding_regions),
                )
            )
        if kv_pair.value:
            print(
                "Value '{}' found within '{}' bounding regions\n".format(
                    kv_pair.value.content,
                    format_bounding_region(kv_pair.value.bounding_regions),
                )
            )

    for page in result.pages:
        print("----Analyzing document from page #{}----".format(page.page_number))
        print(
            "Page has width: {} and height: {}, measured with unit: {}".format(
                page.width, page.height, page.unit
            )
        )

        for line_idx, line in enumerate(page.lines):
            print(
                "...Line # {} has text content '{}' within bounding box '{}'".format(
                    line_idx,
                    line.content,
                    format_polygon(line.polygon),
                )
            )

        for word in page.words:
            print(
                "...Word '{}' has a confidence of {}".format(
                    word.content, word.confidence
                )
            )

        for selection_mark in page.selection_marks:
            print(
                "...Selection mark is '{}' within bounding box '{}' and has a confidence of {}".format(
                    selection_mark.state,
                    format_polygon(selection_mark.polygon),
                    selection_mark.confidence,
                )
            )

    import matplotlib.pyplot as plt

    # get the first page of the document
    page = result.pages[0]

    # set up matplotlib figure and size it to fit 2 columns of text
    plt.figure(figsize=(15, 15))

    # open the image file and draw boxes around detected items
    image = plt.imread("data/00027_original.png")

    # display the image
    plt.imshow(image, cmap="gray")

    for table_idx, table in enumerate(result.tables):
        print(
            "Table # {} has {} rows and {} columns".format(
                table_idx, table.row_count, table.column_count
            )
        )
        for region in table.bounding_regions:
            print(
                "Table # {} location on page: {} is {}".format(
                    table_idx,
                    region.page_number,
                    format_polygon(region.polygon),
                )
            )
        for cell in table.cells:
            print(
                "...Cell[{}][{}] has content '{}'".format(
                    cell.row_index,
                    cell.column_index,
                    cell.content,
                )
            )
            for region in cell.bounding_regions:
                # draw using matplotlib
                plt.gca().add_patch(
                    plt.Polygon(
                        [[point[0] * 300, point[1] * 300] for point in region.polygon],
                        fill=False,
                        color="red",
                        linewidth=1,
                    )
                )

                print(
                    "...content on page {} is within bounding box '{}'\n".format(
                        region.page_number,
                        format_polygon(region.polygon),
                    )
                )

    # save the image
    plt.savefig("annotated_output.png", dpi=300)

    print("----------------------------------------")


if __name__ == "__main__":
    analyze_general_documents()
