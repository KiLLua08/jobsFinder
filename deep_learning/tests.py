from django.test import TestCase
from unittest.mock import patch, MagicMock, PropertyMock
from deep_learning.pipeline import RelevanceClassifier, SkillsExtractor, BatchProcessor, ModelCache
from scraping.models import JobListing


class RelevanceClassifierTest(TestCase):
    def test_empty_text_returns_false(self):
        clf = RelevanceClassifier()
        is_relevant, score = clf.classify("")
        self.assertFalse(is_relevant)
        self.assertEqual(score, 0.0)

    def test_whitespace_only_returns_false(self):
        clf = RelevanceClassifier()
        is_relevant, score = clf.classify("   ")
        self.assertFalse(is_relevant)
        self.assertEqual(score, 0.0)

    def test_high_score_is_relevant(self):
        with patch.object(ModelCache, "classifier", new_callable=PropertyMock) as mock_clf:
            mock_clf.return_value = _mock_classifier(0.8)
            clf = RelevanceClassifier()
            is_relevant, score = clf.classify("We need a Python developer with Django experience.")
        self.assertTrue(is_relevant)
        self.assertGreater(score, 0.55)

    def test_low_score_is_not_relevant(self):
        with patch.object(ModelCache, "classifier", new_callable=PropertyMock) as mock_clf:
            mock_clf.return_value = _mock_classifier(0.2)
            clf = RelevanceClassifier()
            is_relevant, _ = clf.classify("Buy cheap shoes online!")
        self.assertFalse(is_relevant)


def _mock_classifier(relevant_score):
    def _call(text, labels, **kwargs):
        return {
            "labels": ["relevant job posting", "irrelevant content", "spam"],
            "scores": [relevant_score, 0.1, 0.1],
        }
    return MagicMock(side_effect=_call)


class SkillsExtractorTest(TestCase):
    def test_empty_text_returns_empty(self):
        with patch.object(ModelCache, "ner", new_callable=PropertyMock, return_value=MagicMock(return_value=[])):
            ext = SkillsExtractor()
            self.assertEqual(ext.extract(""), [])

    def test_regex_finds_known_skills(self):
        with patch.object(ModelCache, "ner", new_callable=PropertyMock, return_value=MagicMock(return_value=[])):
            ext = SkillsExtractor()
            skills = ext.extract("We use Python, Django, and Docker in production.")
        self.assertIn("Python", skills)
        self.assertIn("Django", skills)
        self.assertIn("Docker", skills)

    def test_normalizes_sql_uppercase(self):
        with patch.object(ModelCache, "ner", new_callable=PropertyMock, return_value=MagicMock(return_value=[])):
            ext = SkillsExtractor()
            skills = ext.extract("Strong SQL skills required.")
        self.assertIn("SQL", skills)

    def test_deduplicates_skills(self):
        with patch.object(ModelCache, "ner", new_callable=PropertyMock, return_value=MagicMock(return_value=[])):
            ext = SkillsExtractor()
            skills = ext.extract("Python python PYTHON")
        self.assertEqual(skills.count("Python"), 1)


class BatchProcessorTest(TestCase):
    def _make_job(self, description="Python and Django developer needed."):
        # Use update() to bypass the post_save signal so nlp_processed stays False
        job = JobListing.objects.create(
            title="Dev", company="Corp",
            description=description,
            link=f"https://example.com/{JobListing.objects.count()}",
            nlp_processed=True,  # create with True to avoid signal
        )
        JobListing.objects.filter(pk=job.pk).update(nlp_processed=False, description=description)
        job.refresh_from_db()
        return job

    def test_process_single_missing_description(self):
        job = JobListing.objects.create(
            title="Dev", company="Corp", description="",
            link="https://example.com/empty",
        )
        processor = BatchProcessor()
        result = processor.process_single(job)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Missing description")

    @patch("deep_learning.pipeline.RelevanceClassifier.classify", return_value=(True, 0.9))
    @patch("deep_learning.pipeline.SkillsExtractor.extract", return_value=["Python", "Django"])
    def test_process_single_success(self, mock_extract, mock_classify):
        job = self._make_job()
        processor = BatchProcessor()
        result = processor.process_single(job)
        self.assertTrue(result["success"])
        self.assertTrue(result["is_relevant"])
        self.assertEqual(result["relevance_score"], 0.9)
        self.assertIn("Python", result["extracted_skills"])

    @patch("deep_learning.pipeline.RelevanceClassifier.classify", return_value=(True, 0.9))
    @patch("deep_learning.pipeline.SkillsExtractor.extract", return_value=["Python"])
    def test_process_batch_updates_db(self, mock_extract, mock_classify):
        job = self._make_job()
        processor = BatchProcessor()
        summary = processor.process_batch(limit=1)
        self.assertEqual(summary["successful"], 1)
        job.refresh_from_db()
        self.assertTrue(job.nlp_processed)
        self.assertTrue(job.is_relevant)
