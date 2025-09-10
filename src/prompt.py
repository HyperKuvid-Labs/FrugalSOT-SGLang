import nltk
from nltk import word_tokenize, pos_tag, ne_chunk, sent_tokenize

# Download models once when module loads (moved outside function)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
nltk.download('maxent_ne_chunker_tab', quiet=True)

# Global sets for efficiency
MODAL_VERBS = {'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would'}
QUESTION_WORDS = {'what', 'where', 'when', 'why', 'how', 'who', 'which'}
NEGATION_WORDS = {'not', 'no', 'never', 'nothing', 'nobody', 'nowhere', 'neither'}
COMPARATIVE_TAGS = {'JJR', 'JJS', 'RBR', 'RBS'}
TECHNICAL_PREFIXES = {'bio', 'micro', 'nano', 'cyber', 'neuro', 'crypto', 'quantum'}

def calculate_tree_depth(tree):
    """Calculate maximum depth of NLTK tree structure"""
    if not hasattr(tree, 'label'):
        return 0
    if len(tree) == 0:
        return 1
    
    child_depths = [calculate_tree_depth(child) for child in tree if hasattr(child, 'label')]
    if not child_depths:
        return 1
    return 1 + max(child_depths)

def classify_prompt_complexity(prompt):
    # Tokenization and POS tagging
    tokens = word_tokenize(prompt)
    pos_tags = pos_tag(tokens)
    ner_tree = ne_chunk(pos_tags)
    sentences = sent_tokenize(prompt)
    
    # 1. LENGTH COMPLEXITY (Original)
    length = len(prompt.split())
    if length <= 5:
        length_complexity = "Low"
    elif 6 <= length <= 15:
        length_complexity = "Mid"
    else:   
        length_complexity = "High"

    # 2. NER COMPLEXITY (Original)
    entity_count = sum(1 for chunk in ner_tree if hasattr(chunk, 'label'))
    if entity_count == 0:
        ner_complexity = "Low"
    elif entity_count <= 2:
        ner_complexity = "Mid"
    else:
        ner_complexity = "High"

    # 3. SYNTACTIC COMPLEXITY (Original - Enhanced)
    conj_count = sum(1 for word, tag in pos_tags if tag == 'CC')
    sub_clause_count = sum(1 for word, tag in pos_tags if tag in {'IN', 'TO'})
    num_sentences = len(sentences)
    avg_sentence_length = len(tokens) / num_sentences if num_sentences > 0 else 0
    
    complexity_score = conj_count + sub_clause_count + (1 if avg_sentence_length > 15 else 0)
    if complexity_score == 0:
        syntax_complexity = "Low"
    elif 1 <= complexity_score <= 3:
        syntax_complexity = "Mid"
    else:
        syntax_complexity = "High"

    # 4. DEPENDENCY PARSE DEPTH
    parse_depth = calculate_tree_depth(ner_tree)
    if parse_depth <= 2:
        depth_complexity = "Low"
    elif parse_depth <= 4:
        depth_complexity = "Mid"
    else:
        depth_complexity = "High"

    # 5. QUESTION TYPE COMPLEXITY
    question_count = sum(1 for word, _ in pos_tags if word.lower() in QUESTION_WORDS)
    wh_question_count = sum(1 for word, _ in pos_tags if word.lower() in {'why', 'how'})
    
    if question_count == 0:
        question_complexity = "Low"
    elif question_count == 1 and wh_question_count == 0:
        question_complexity = "Mid"
    else:
        question_complexity = "High"

    # 6. AMBIGUITY SCORE
    ambiguous_words = sum(1 for word, tag in pos_tags if len(word) > 3 and 
                         any(t in tag for t in ['NN', 'VB']) and word.lower() not in MODAL_VERBS)
    polysemous_count = len([word for word, _ in pos_tags if len(word) > 4])
    
    ambiguity_score = ambiguous_words + (polysemous_count // 3)
    if ambiguity_score <= 2:
        ambiguity_complexity = "Low"
    elif ambiguity_score <= 5:
        ambiguity_complexity = "Mid"
    else:
        ambiguity_complexity = "High"

    # 7. INFERENCE REQUIREMENTS
    modal_count = sum(1 for word, _ in pos_tags if word.lower() in MODAL_VERBS)
    conditional_words = sum(1 for word, _ in pos_tags if word.lower() in {'if', 'unless', 'assuming', 'given'})
    causal_words = sum(1 for word, _ in pos_tags if word.lower() in {'because', 'since', 'therefore', 'thus'})
    
    inference_score = modal_count + conditional_words + causal_words + (conj_count // 2)
    if inference_score <= 1:
        inference_complexity = "Low"
    elif inference_score <= 3:
        inference_complexity = "Mid"
    else:
        inference_complexity = "High"

    # 8. TECHNICAL TERM DENSITY
    technical_count = 0
    for word, tag in pos_tags:
        word_lower = word.lower()
        # Technical indicators: capitalized non-proper nouns, technical prefixes, long technical words
        if (word[0].isupper() and tag not in {'NNP', 'NNPS'} and len(word) > 3) or \
           any(word_lower.startswith(prefix) for prefix in TECHNICAL_PREFIXES) or \
           (len(word) > 8 and tag.startswith('NN')):
            technical_count += 1
    
    technical_density = technical_count / len(tokens) if len(tokens) > 0 else 0
    if technical_density <= 0.1:
        technical_complexity = "Low"
    elif technical_density <= 0.3:
        technical_complexity = "Mid"
    else:
        technical_complexity = "High"

    # 9. CLAUSE NESTING LEVEL
    relative_pronouns = sum(1 for word, tag in pos_tags if word.lower() in {'that', 'which', 'who', 'whom', 'whose'})
    nested_structures = sub_clause_count + relative_pronouns
    
    if nested_structures <= 1:
        nesting_complexity = "Low"
    elif nested_structures <= 3:
        nesting_complexity = "Mid"
    else:
        nesting_complexity = "High"

    # 10. LEXICAL DIVERSITY (TTR)
    unique_words = len(set(token.lower() for token in tokens if token.isalpha()))
    total_words = len([token for token in tokens if token.isalpha()])
    ttr = unique_words / total_words if total_words > 0 else 0
    
    if ttr <= 0.6:
        diversity_complexity = "Low"
    elif ttr <= 0.8:
        diversity_complexity = "Mid"
    else:
        diversity_complexity = "High"

    # WEIGHTED SCORING SYSTEM
    weights = {"Low": 0, "Mid": 2, "High": 4}
    
    # Calculate weighted scores with importance-based multipliers
    total_score = (
        weights[length_complexity] * 1 +      # Base metric
        weights[ner_complexity] * 3 +         # High importance - knowledge requirements
        weights[syntax_complexity] * 3 +      # High importance - parsing difficulty
        weights[depth_complexity] * 3 +       # High importance - structural complexity
        weights[question_complexity] * 2 +    # Medium importance - response strategy
        weights[ambiguity_complexity] * 3 +   # High importance - interpretation difficulty
        weights[inference_complexity] * 3 +   # High importance - reasoning requirements
        weights[technical_complexity] * 3 +   # High importance - domain knowledge
        weights[nesting_complexity] * 2 +     # Medium importance - structural parsing
        weights[diversity_complexity] * 1     # Low importance - vocabulary breadth
    )

    # Final complexity classification with adjusted thresholds
    if total_score <= 15:
        majority_complexity = "Low"
    elif 16 <= total_score <= 35:
        majority_complexity = "Mid"
    else:
        majority_complexity = "High"

    # Enhanced output with all metrics
    print(f"Prompt: {prompt}")
    print(f"Length: {length_complexity} | NER: {ner_complexity} | Syntactic: {syntax_complexity}")
    print(f"Parse Depth: {depth_complexity} | Question Type: {question_complexity} | Ambiguity: {ambiguity_complexity}")
    print(f"Inference: {inference_complexity} | Technical: {technical_complexity} | Nesting: {nesting_complexity} | Diversity: {diversity_complexity}")
    print(f"Total Score: {total_score} | Final Complexity: {majority_complexity}\n")
    
    return majority_complexity
