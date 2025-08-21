#let poster(
  // set variables for use throughout
  // note: some are referenced from `.qmd` file
  size: "'36x24' or '48x36''",
  title: "Paper Title",
  authors: "Author Names (separated by commas)",
  departments: "Department Name",
  univ_logo: "Logo Path",
  footer_text: " ",
  footer_url: "Footer URL",
  footer_email_ids: "Email IDs (separated by commas)",
  footer_color: "Hex Color Code",
  keywords: (),
  num_columns: "4",
  univ_logo_scale: "185",
  univ_logo_column_size: "13",
  title_column_size: "22",
  title_font_size: "48",
  authors_font_size: "36",
  footer_url_font_size: "40",
  footer_text_font_size: "40",
  body
) = {
  // initialize template display formatting
  set text(font: "Lato", size: 26pt)
  let sizes = size.split("x")
  let width = int(sizes.at(0)) * 1in
  let height = int(sizes.at(1)) * 1in
  univ_logo_scale = int(univ_logo_scale) * 1%
  title_font_size = int(title_font_size) * 1pt
  authors_font_size = int(authors_font_size) * 1pt
  num_columns = int(num_columns)
  univ_logo_column_size = int(univ_logo_column_size) * 1in
  title_column_size = int(title_column_size) * 1in
  footer_url_font_size = int(footer_url_font_size) * 1pt
  footer_text_font_size = int(footer_text_font_size) * 1pt

  // create overall page output
  set page(
    // total dimensions
    width: width,
    height: height,
    // margin on all sides
    margin:
      (top: .8in, left: .8in, right: .8in, bottom: 1.8in),
    // footer section
    footer: [
      #set align(center)
      #set text(42pt)
      #block(
        fill: rgb(footer_color),
        width: 100%,
        inset: 20pt,
        radius: 10pt,
        // adds text to footer
        [
          #text(font: "Lato", size: footer_url_font_size, footer_url)
          #h(1fr)
          #text(size: footer_text_font_size, smallcaps(footer_text))
          #h(1fr)
          #text(font: "Lato", size: footer_url_font_size, footer_email_ids)
        ]
      )
    ]
  )

  // set math display properties
  set math.equation(numbering: "(1)")
  show math.equation: set block(spacing: 0.65em)

  set enum(indent: 10pt, body-indent: 9pt)
  set list(indent: 10pt, body-indent: 9pt)

  // set the heading numbering system
  set heading(numbering: "I.A.1.")
  show heading: it => context {
    // Get numbering tuple for *this* heading at the current location.
    let levels = counter(heading).at(here())
    let deepest = if levels != () { levels.last() } else { 1 }

    // defines how sub-headers display
    set text(24pt, weight: 400)

    // sub-header level 0
    if it.level == 0 [
      #set text(style: "italic")
      #v(32pt, weak: true)
      #if it.numbering != none {
        numbering("i.", deepest)
        h(7pt, weak: true)
      }
      #it.body

    // sub-header level 1
    ] else if it.level == 1 [
      #v(10pt, weak: true)
      #set align(left)
      #set text({ 40pt }, weight: 600, font: "Vollkorn", fill: rgb("#246876"))
      #v(50pt, weak: true)
      #if it.numbering != none {
        numbering("I.", deepest)
        h(7pt, weak: true)
      }
      #it.body
      #v(30pt, weak: true)
      #line(length: 100%, stroke: rgb(200, 200, 200))
      #v(30pt, weak: true)

    // all other headers
    ] else [
      #set text({ 36pt }, weight: 600, font: "Vollkorn", fill: rgb("#1e4b5c"), style: "italic")
      #if it.level == 2 {
        numbering("❀  a)", deepest)
        [ ]
      }
      #it.body
      #v(40pt, weak: true)
    ]
}

  // header grid
  align(left,
    grid(
      // rows and cols in the header
      rows: (auto, auto),
      columns: (title_column_size, univ_logo_column_size),
      column-gutter: 5pt,
      row-gutter: 30pt,
      // main title
      image("./images/title-text.png", width: 65%),
      grid.cell(
        pad(top: 20pt,
          image(univ_logo, width: univ_logo_scale),
        ),
        rowspan: 3,
        align: left,
      ),
      // author display
      text(size: 28pt, authors),
      // department and notes display
      text(size: 25pt, emph(departments)),
    )
  )

  // spacing between the header and body
  v(40pt)

  // set main body display
  show: columns.with(num_columns, gutter: 60pt)
  // paragraph display properties
  set par(leading: 10pt,
    justify: false,
    first-line-indent: 0em,
    linebreaks: "optimized"
  )

  // Configure figures.
  show figure: it => block({
    // Display a backdrop rectangle.
    it.body

    // Display caption.
    if it.has("caption") {
      set align(left)
      v(if it.has("gap") { it.gap } else { 24pt }, weak: true)
      set text(weight: "bold")
      it.caption
    }

  })

  // adds body content to page
  body
}
