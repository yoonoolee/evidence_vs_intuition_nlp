# Evidence versus Intuition Rhetoric in U.S. House of Representatives

A BERT-based analysis examining how constituent education levels affect House Representatives' use of evidence-based versus intuition-based language in congressional hearings (Congress 112-118).

**Authors:** Avery Lee, Patrick Ruan, Sanjali Roy
**Institution:** University of California, Berkeley

For full research details, see the [paper](A%20Bert-based%20Analysis%20of%20Evidence%20versus%20Intuition%20Rhetoric%20in%20U.S.%20House%20of%20Representatives%20and%20Constituent%20Education%20Levels.pdf).

The main analysis script is in `Modeling/Evidence_and_Intuition_vs_Education.ipynb`.

## Repository Structure

```
├── Data/
│   ├── Intermediate/                              # Intermediate outputs from main modeling script
│   ├── House_Members/                             # House of Representatives information
│   ├── Transcript_Scraped/                        # Transcripts in txt format for all committees (Congress 112-118)
│   └── US_Census_Education_By_District/           # US district education census data
│
├── Data Preprocessing/                            # Scripts for cleaning original datasets
│
├── Modeling/
│   └── Evidence_and_Intuition_vs_Education.ipynb  # Main project script
│
├── Plots and Graphs/                              # Plot images
│
└── A Bert-based Analysis of Evidence versus Intuition Rhetoric in U.S. House of Representatives and Constituent Education Levels.pdf
```

## License

This project is for academic research purposes.
