# Evidence versus Intuition Rhetoric in U.S. House of Representatives

A BERT-based analysis examining how constituent education levels affect House Representatives' use of evidence-based versus intuition-based language in congressional hearings (congression session 112-118).

**Authors:** Avery Lee, Patrick Ruan, Sanjali Roy
**Institution:** University of California, Berkeley

## Abstract

This study explores whether constituent education level affects House of Representatives' use of evidence-based versus intuition-based language in house hearings, using dictionary-based SemAxis methods and fine-tuning a BERT regression model. Although we find no meaningful correlation between constituent education level and representative rhetoric in the constituents' absence to observe unbiased speaking style, we discovered with mixed-effects regression that variation in evidence-based and intuition-based language is largely explained by differences between individual representatives, rather than their constituent education level or the party they belong to.

## Data

The dataset merges three data sources spanning Congress 112 to 118 (2011-2024):

1. **Congressional House Hearing Transcripts** - Obtained from GovInfo (U.S. Government Publishing Office)
   - House committees discuss legislation proposals, conduct investigations, or evaluate government activities
   - Extracted at sentence level with representative metadata

2. **House of Representatives Dataset** - Contains representative state, district, congressional session, and party affiliation

3. **US Census Education Dataset** - Provides district-level population counts and education attainment
   - Number of people with bachelor's, master's, professional school, and doctorate degrees
   - Mean percentage of higher education calculated per district for each congressional session

**Final Dataset:**
- Approximately 5.4 million sentences
- 2,764 unique aggregated (state/district/congress) combinations
- Features: first name, last name, state, party, congress, district, dialogue, and bachelor's or higher percentages

## Methods

### 1. Tokenization and Word2Vec Training
- Tokenization using SpaCy's english model (en-core-web-sm)
- Word2Vec model trained with skip-gram architecture
  - 300-dimensional vectors
  - Context window of 10 tokens
  - Minimum word frequency of 5
  - 20 training epochs

### 2. Semantic Axis Construction with SemAxis
- Constructs bipolar axis between intuition versus evidence language
- Seed dictionaries: 48 evidence seed words and 32 intuition seed words
- Seeds expanded using cosine similarity (>0.75 for pole seeds, <0.35 for opposing pole)
- Positive values indicate evidence-based language, negative values indicate intuition-based language

### 3. Sentence-Level Scoring with TF-IDF
- Sentence-level scores computed by aggregating word-level SemAxis scores weighted by TF-IDF
- Accounts for words with different semantic significance

### 4. BERT Fine-tuning
- English BERT-base-uncased regression model fine-tuned on normalized SemAxis sentence scores
- Min-max normalization to [0, 1] scale
- Dataset stratified into 5 bins: very intuition [0, 0.2), intuition [0.2, 0.4), mixed [0.4, 0.6), evidence [0.6, 0.8), very evidence [0.8, 1.0]
- Train/validation/test split: 70%/15%/15%
- Mean Absolute Error (MAE) used as evaluation metric
- Trained for 3 epochs with batch sizes of 64 (training) and 128 (evaluation)

### 5. Model Validation
- 200 sentences (40 per bin) independently labeled by three annotators on 0-5 scale
- Krippendorff's alpha: 0.802 (high inter-annotator agreement)
- SemAxis: Pearson r = 0.866, MAE = 0.1105
- BERT: Pearson r = 0.864, MAE = 0.1108
- Both models achieve 56.8% improvement over baseline

### 6. Mixed-Effects Regression
- Accounts for hierarchical clustering structure (multiple sentences from same representative across parties and sessions)
- Groups by party, then individual representative level
- Analyzes both fixed and random effects

## Key Findings

1. **No Meaningful Correlation with Education Level**
   - SemAxis: r = -0.046, R² = 0.0021
   - BERT: r = -0.047, R² = 0.0022
   - No meaningful predictive relationship between constituent education levels and representative rhetoric in house hearings

2. **Individual Representatives Drive Variation**
   - 81.2% of variance in rhetoric scores is between individual representatives
   - Only 18.8% is within an individual representative
   - Which representative is speaking matters more than constituent education level or party affiliation

3. **Party-Level Effects Minimal**
   - 50% of variance in rhetoric scores is between parties
   - 50% is within parties
   - Nearly flat slope with high p-value (0.863 for SemAxis, 0.859 for BERT)

4. **BERT vs SemAxis Performance**
   - Both models perform nearly identically (Pearson correlation = 0.9996)
   - BERT regression using context is viable for rating rhetoric in dialogue-based datasets

## Repository Structure

```
├── Data/                          # Data files
├── Data Preprocessing/            # Preprocessing scripts
├── Modeling/                      # Jupyter notebooks with analysis
│   └── Evidence_and_Intuition_vs_Education.ipynb
├── Plots and Graphs/              # Visualizations
└── A Bert-based Analysis....pdf   # Full research paper
```

## Requirements

- Python 3.x
- SpaCy (en-core-web-sm model)
- Gensim (Word2Vec)
- Transformers (BERT)
- scikit-learn
- pandas
- numpy
- matplotlib
- scipy

## License

This project is for academic research purposes.
