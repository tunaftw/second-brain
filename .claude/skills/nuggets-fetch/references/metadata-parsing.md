# Metadata Parsing

## Guest Extraction from Title

Common patterns:

| Pattern | Example | Extracted Guest |
|---------|---------|-----------------|
| "with {Guest}" | "Sleep Tips with Dr. Matt Walker" | Dr. Matt Walker |
| "{Guest}: Topic" | "Andy Galpin: How to Build Muscle" | Andy Galpin |
| "{Guest} - Topic" | "David Goggins - Mental Toughness" | David Goggins |
| "#{Number} {Guest}" | "#1892 David Goggins" | David Goggins |

## Host Detection from Channel

| Channel | Host |
|---------|------|
| Huberman Lab | Andrew Huberman |
| The Joe Rogan Experience | Joe Rogan |
| Modern Wisdom | Chris Williamson |
| Diary of a CEO | Steven Bartlett |
| Lex Fridman Podcast | Lex Fridman |
| The Tim Ferriss Show | Tim Ferriss |
| Jay Shetty Podcast | Jay Shetty |
