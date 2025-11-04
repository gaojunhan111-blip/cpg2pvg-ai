"""
SpaCy Mock Module
用于在缺少spaCy依赖时提供基本功能
"""

class MockSpacy:
    """模拟SpaCy模块"""

    class __version__:
        version = "3.4.0"

    def load(self, model_name):
        return MockNLP()

    def blank(self, lang_code):
        return MockNLP()

    def __getattr__(self, name):
        if name == "__version__":
            return self.__version__
        return MockSpacy()


class MockNLP:
    """模拟SpaCy NLP对象"""

    def __init__(self):
        self.vocab = MockVocab()

    def __call__(self, text):
        return MockDoc(text)

    def pipe(self, texts, **kwargs):
        return [MockDoc(text) for text in texts]

    def disable_pipes(self, *pipe_names):
        return self


class MockVocab:
    """模拟SpaCy词汇表"""

    def __init__(self):
        self.strings = MockStrings()


class MockStrings:
    """模拟SpaCy字符串存储"""

    def add(self, text):
        return hash(text)


class MockDoc:
    """模拟SpaCy文档对象"""

    def __init__(self, text):
        self.text = text
        self.ents = self._extract_entities(text)

    def _extract_entities(self, text):
        """简单的实体提取模拟"""
        # 简单的医学关键词检测
        medical_keywords = {
            "diabetes": "DISEASE",
            "hypertension": "DISEASE",
            "metformin": "MEDICATION",
            "insulin": "MEDICATION",
            "headache": "SYMPTOM",
            "fever": "SYMPTOM",
            "blood pressure": "LAB_TEST",
            "glucose": "LAB_TEST"
        }

        ents = []
        for keyword, label in medical_keywords.items():
            start_idx = text.lower().find(keyword.lower())
            if start_idx != -1:
                ents.append(MockSpan(text, start_idx, start_idx + len(keyword), label))

        return ents

    def __iter__(self):
        words = self.text.split()
        for i, word in enumerate(words):
            yield MockToken(word, i)

    def __len__(self):
        return len(self.text.split())

    def to_json(self):
        return {"text": self.text}


class MockSpan:
    """模拟SpaCy实体"""

    def __init__(self, text, start, end, label):
        self.text = text[start:end]
        self.start_char = start
        self.end_char = end
        self.label_ = label

    def __repr__(self):
        return f"MockSpan(text='{self.text}', label='{self.label_}')"


class MockToken:
    """模拟SpaCy词元"""

    def __init__(self, text, idx):
        self.text = text
        self.idx = idx
        self.i = idx
        self.pos_ = "NOUN"  # 默认词性
        self.lemma_ = text.lower()
        self.is_alpha = text.isalpha()
        self.is_stop = text.lower() in ["the", "a", "an", "and", "or", "but"]
        self.is_punct = not text.isalpha()

    def __repr__(self):
        return f"MockToken(text='{self.text}')"


class MockMatcher:
    """模拟SpaCy匹配器"""

    def __init__(self, vocab):
        self.vocab = vocab
        self.rules = []

    def add(self, rule_name, patterns):
        self.rules.append((rule_name, patterns))

    def __call__(self, doc):
        matches = []
        for rule_name, patterns in self.rules:
            for pattern in patterns:
                # 简单的模式匹配
                if isinstance(pattern, list):
                    pattern_text = " ".join([p.get("LOWER", "") if isinstance(p, dict) else str(p) for p in pattern])
                    if pattern_text in doc.text.lower():
                        start = doc.text.lower().find(pattern_text)
                        if start != -1:
                            matches.append((self.rules.index((rule_name, patterns)), start, start + len(pattern_text)))
        return matches


# 创建模拟的spaCy模块
spacy = MockSpacy()
nlp = MockNLP()
Matcher = MockMatcher