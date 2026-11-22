---
name: "MediSupply"
description: "A clear pharmacy ordering and distribution workspace."
colors:
  navy: "#172e43"
  navy-active: "#29485f"
  teal: "#177b70"
  teal-dark: "#10675e"
  teal-wash: "#e9f4f0"
  ink: "#23394a"
  muted: "#60717f"
  ground: "#f4f6f7"
  line: "#e0e6e9"
  white: "#fff"
  danger: "#a53637"
  danger-wash: "#fff0ed"
  amber: "#8c5a12"
  amber-wash: "#fff5e4"
  focus: "#40a99c"
  control-line: "#ccd6db"
  submitted: "#4b6681"
  submitted-wash: "#edf2f7"
  processing: "#875b12"
  processing-wash: "#fff3dc"
  shipped: "#4866a2"
  shipped-wash: "#eaf0fc"
  positive: "#35714b"
  positive-wash: "#e9f4ec"
  cancelled: "#53616c"
  cancelled-wash: "#eef0f2"
typography:
  display:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "clamp(44px, 4.3vw, 65px)"
    fontWeight: 500
    lineHeight: 1.12
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  section-title:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  table-body:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
  table-label:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.5
  metric:
    fontFamily: "Plex, 'Segoe UI', sans-serif"
    fontSize: "30px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.035em"
rounded:
  badge: "4px"
  control: "6px"
  toast: "8px"
  panel: "12px"
  circle: "50%"
spacing:
  "4": "4px"
  "6": "6px"
  "8": "8px"
  "12": "12px"
  "16": "16px"
  "18": "18px"
  "20": "20px"
  "24": "24px"
  "28": "28px"
  "36": "36px"
components:
  button-primary:
    backgroundColor: "{colors.teal}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  button-primary-hover:
    backgroundColor: "{colors.teal-dark}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  button-danger:
    backgroundColor: "{colors.danger-wash}"
    textColor: "{colors.danger}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  button-add:
    backgroundColor: "{colors.teal-wash}"
    textColor: "{colors.teal-dark}"
    rounded: "{rounded.control}"
    padding: "7px 10px"
  button-text:
    textColor: "{colors.teal-dark}"
    padding: "4px 0"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "9px 12px"
  nav-active:
    backgroundColor: "{colors.navy-active}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "12px 13px"
  badge-submitted:
    backgroundColor: "{colors.submitted-wash}"
    textColor: "{colors.submitted}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-processing:
    backgroundColor: "{colors.processing-wash}"
    textColor: "{colors.processing}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-shipped:
    backgroundColor: "{colors.shipped-wash}"
    textColor: "{colors.shipped}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-positive:
    backgroundColor: "{colors.positive-wash}"
    textColor: "{colors.positive}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-cancelled:
    backgroundColor: "{colors.cancelled-wash}"
    textColor: "{colors.cancelled}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-warning:
    backgroundColor: "{colors.amber-wash}"
    textColor: "{colors.amber}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  badge-critical:
    backgroundColor: "{colors.danger-wash}"
    textColor: "{colors.danger}"
    rounded: "{rounded.badge}"
    padding: "5px 8px"
  panel:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  tracking-current:
    backgroundColor: "{colors.teal}"
    textColor: "{colors.white}"
    rounded: "{rounded.circle}"
    size: "36px"
---

# Design System: MediSupply

## Overview

**Creative North Star: "The Distribution Service Guide"**

The Distribution Service Guide gives MediSupply a steady, legible working identity. Ink-navy navigation anchors white work surfaces on a cool pale ground; forest and eucalyptus colors identify actions and progress. Light rules, aligned figures, and modest corner rounding support repeated scanning of medication, pack, price, lot, and order information.

IBM Plex Sans carries the entire interface. The product's visual character comes from consistent density and restrained state changes, with a connected fulfillment strip as its recurring progress pattern. Native controls, explicit labels, and text-bearing statuses keep the interface familiar. Motion is brief feedback for an action.

**Key Characteristics:**

- Ink-navy identity with forest and eucalyptus action colors.
- Compact tables, tabular figures, and explicit status text.
- Flat white panels separated by light rules and a cool ground.
- Native form controls and a connected fulfillment strip.

This record is extracted from `static/styles.css`, `static/app.js`, and the self-hosted font files. The portal's surface composition and mode remain in `.impeccable/surfaces/portal.md`. Frontmatter records implemented primitives; the sidecar adds responsive, motion, elevation, and preview metadata.

## Colors

The palette combines ink-navy structure, eucalyptus actions, cool neutrals, and distinct operational status colors. Frontmatter is the normative value list.

### Primary

- **Eucalyptus** (`teal`): primary actions, current fulfillment stage, and selected filter accents.
- **Forest** (`teal-dark`): text actions and primary-button hover.
- **Eucalyptus wash** (`teal-wash`): compact Add actions, cart counts, and completed progress markers.

### Secondary

- **Ink navy** (`navy`): the navigation rail and sign-in identity area.
- **Active navy** (`navy-active`): the selected navigation destination.

### Neutral

- **Ink** (`ink`) and **slate** (`muted`): primary information and supporting descriptions.
- **Cool ground** (`ground`) and **white** (`white`): the page and working surfaces.
- **Light rule** (`line`) and **control rule** (`control-line`): panel/table separation and native field boundaries.
- **Focus eucalyptus** (`focus`): the shared keyboard-focus outline.

### Status mapping

| Meaning | Text token | Surface token |
| --- | --- | --- |
| Submitted | `submitted` | `submitted-wash` |
| Processing | `processing` | `processing-wash` |
| Shipped | `shipped` | `shipped-wash` |
| Delivered / In stock | `positive` | `positive-wash` |
| Cancelled | `cancelled` | `cancelled-wash` |
| Low stock | `amber` | `amber-wash` |
| Expired / Out of stock | `danger` | `danger-wash` |

Danger also identifies destructive actions and inline errors. Amber calls attention to inventory exceptions. The sidecar's generated tonal ramps are preview aids, not additional implemented palette steps.

**The Text-Bearing Status Rule.** Every status pairs its color with a readable label; color and the small dot are supporting signals.

## Typography

**Display and Body Font:** IBM Plex Sans, registered locally as `Plex`, with `Segoe UI` and generic sans-serif fallbacks. Four WOFF2 files in `static/fonts/` provide weights 400, 500, 600, and 700 with `font-display: swap`; the interface does not depend on a remote font service.

The humanist family stays readable in dense operational content. Regular text carries detail, medium weights identify controls, and semibold weights establish headings and totals. The type scale is chosen by role rather than a fixed mathematical ratio. The root disables font synthesis and uses tabular numerals.

### Hierarchy

- **Display:** the sign-in story uses the fluid display token. It resolves to 46px at the 950px breakpoint; the story content is hidden at 720px.
- **Headline:** page titles use the headline token, decreasing to 28px at 1250px and 27px at 720px.
- **Title / section title:** general headings use the title token; recurring panel headings use the smaller section-title token.
- **Body:** the root uses the body token; table content uses table-body. Supporting interface copy typically sits between these roles (12–13px). Paragraphs are limited to 72ch where space allows.
- **Label:** native form labels use the label token. Table headers use table-label, with medium weight and sentence case.
- **Metric:** overview totals use the metric token, changing to 27px on narrower layouts and 34px from 1550px.

Headings use tight tracking and balanced wrapping. Small metadata remains subordinate; it does not replace labels or primary content.

**The Aligned Figures Rule.** Use tabular numerals throughout and right-align price, quantity, and total columns.

## Layout

The desktop shell has a fixed navy navigation rail (235px) and a white account bar (85px). The main region fills the remaining width, has a 1650px maximum, and uses 36px horizontal gutters. Repeated panels are separated by 24px; their common inner padding is 24px. Dense controls use smaller 6–12px gaps. Spacing is practical and task-led, with the recurring steps recorded in frontmatter.

Summary strips divide a shared surface into columns. Tables retain their native structure, caption, header row, and aligned numeric cells. Desktop headers use 12px vertical padding and data rows 16px; catalog rows use 20px. Horizontal cell padding is generally 18px, with 24px outer edges. Tables keep content on one line and scroll inside their own region when needed. Each region receives a keyboard tab stop and accessible name from its caption.

| Viewport condition | Implemented change |
| --- | --- |
| At least 1550px | More top breathing room (44px), wider dashboard proportion, and larger summary figures. |
| At most 1250px | Rail narrows to 210px; content gutters become 24px; dashboard and cart columns stack; catalog filters reflow. |
| At most 950px | Rail narrows to 185px; overview metrics become two columns; order detail stacks, with paired side panels where room remains. |
| At most 720px | Navigation becomes a four-item row above content; the rail stops being fixed; the account bar is 66px; content gutters become 18px; page headings wrap; filters and side panels reflow; inventory summaries become two columns. |

The four navigation destinations are Overview, Medication catalog, Orders & tracking, and Inventory. Order cart is a separate account-bar destination. On mobile, navigation uses text and icons, while account identity in the rail gives way to the sign-out control and the persistent account bar. The sign-in layout changes from two columns to a compact brand band above the form. Long tables remain contained instead of shrinking all columns into unreadable cells.

## Elevation & Depth

Ordinary working surfaces are flat. White panels, the cool page ground, fine borders, and state washes establish separation. Three small shadow roles exist: the selected sign-in role (`0 2px 4px #00000010`), toast feedback (`0 6px 24px #00000026`), and modal dialogs (`0 16px 65px #00000035`). The dialog backdrop is a translucent navy (`#112a426b`).

**The Flat Work Surface Rule.** Keep ordinary panels and tables free of shadows; reserve elevation for the selected sign-in role, notifications, and modal dialogs.

## Shapes

Controls and navigation items use the control radius; panels and dialogs use the panel radius. Status badges use the smaller badge radius, and toasts use the toast radius. Circular marks identify account initials, counts, status dots, and fulfillment stops. Thin solid boundaries provide structure. The form language stays modest and consistent without pill-shaped primary buttons.

Icons are inline, unfilled SVG line drawings with rounded caps and joins, normally using a 1.6px stroke on a 24-unit view box. Their size follows the control or information role. Icons supplement readable labels; icon-only actions have accessible names.

## Components

### Buttons

Primary, secondary, destructive, compact Add, and text actions share one visual language. Standard buttons use medium 13px type, a minimum height of 41px, and the control radius. Primary uses eucalyptus with white text; hover deepens to forest. Secondary uses white with a light stroke and a pale green hover. Destructive actions use the danger wash with a warm border. Compact Add buttons use eucalyptus wash, 11px type, and a 33px minimum height. Text actions underline on hover.

Button background and border transitions take 150ms with CSS's default ease. Disabled buttons reduce opacity to 0.45 and use a not-allowed cursor. Pending form submissions disable the submitting control and mark it busy. The shared focus-visible outline is 3px with a 3px offset.

### Inputs / Fields

Inputs, native selects, and textareas use white surfaces, a thin control rule, and the control radius. The general minimum height is 40px; sign-in fields use 44px. Borders darken on hover through a 150ms transition. Search fields reserve space for an inline SVG. Quantity controls remain native number inputs. Textareas resize vertically.

Every field has a label, either visible or visually hidden. Native required, type, minimum, step, and length validation stays available. Inline form errors use danger text and an alert role; they do not depend on a border-color change. Retain the shared focus outline and the visible caret.

### Navigation

Desktop navigation presents an icon and label in a minimum 44px row. Active items use active navy, white text, medium weight, a small eucalyptus marker, and `aria-current`. Hover adds a lighter navy surface. Mobile destinations stack icon above label with a minimum 55px height. Order-status filters use native links with count chips, an underline for selection, and their own horizontal scrolling strip.

### Status badges

Badges combine a small circular dot, readable status text, a soft fill, and compact padding. The dot inherits text color. They are informational rather than buttons. Preserve the semantic mapping in Colors when adding another view of the same order or stock state.

### Panels and tables

Panels use a white surface, a light border, the panel radius, and clipped corners. Section headings provide a title and an optional action; dense data occupies the space below. Table headers have a subtly tinted background, rows have fine horizontal rules, and hover adds only a very light fill. Prices and quantities align to the right. Order identifiers are forest text links with underlines on hover.

### Connected fulfillment strip

An ordered list links Submitted, Processing, Shipped, and Delivered through four circular stops. Reached stages use pale eucalyptus markers and a tinted connecting line. The current marker is solid eucalyptus with white iconography. Completed stages use a check icon. Each stage also says Complete, Current status, or Upcoming. A cancelled order replaces the strip with an explicit cancellation message while keeping its history.

### Dialogs, feedback, and motion

Cancellation confirmation and stock adjustment use the native modal `dialog`, opened with `showModal()`. Dialogs are constrained to the viewport with a maximum width of 460px and 16px side clearance. Titles, close controls, form errors, and actions are explicit.

Notifications appear near the bottom center, with a dismiss control and a polite live announcement. They dismiss after 6500ms. Arrival takes 250ms using `cubic-bezier(.16,1,.3,1)`: an 8px upward move, opacity from 0.2, and a small clip reveal. Success uses deep green; errors use deep red. Under `prefers-reduced-motion: reduce`, animation and transitions are removed and scroll behavior is automatic.

Empty states contain a title, short explanation, and recovery action where one exists. Loading uses text and busy semantics. The page provides a skip link and moves focus to the main region after navigation.

## Do's and Don'ts

### Do:

- Do use the established navy, teal, neutral, and status roles for their existing purposes.
- Do keep prices, pack quantities, totals, and dates easy to compare with tabular figures.
- Do retain native labeled controls, visible keyboard focus, and text for every status.
- Do contain wide tables inside labeled, keyboard-focusable horizontal scroll regions.
- Do preserve the compact control scale and the larger panel spacing as separate levels of density.
- Do disable repeated submissions while a request is pending and show errors close to the relevant form.

### Don't:

- Don't turn ordinary data panels into floating cards with shadows.
- Don't replace native selects, numeric inputs, or dialogs with decorative imitations.
- Don't use color alone to communicate availability or order progress.
- Don't let a wide table force the whole page to scroll horizontally.
- Don't extend the brief notification animation into continuous or ambient motion.
