import unittest
from pathlib import Path


class FDP2LitePublicationTablesFiguresTests(unittest.TestCase):
    def test_generator_has_headless_deterministic_publication_contract(self):
        script = Path(
            "docs/superpowers/figures/fd-p2-lite/"
            "make_fd_p2_lite_publication_tables_figures.py"
        )
        self.assertTrue(script.exists(), f"{script} is missing")

        source = script.read_text()
        required_snippets = [
            'matplotlib.use("Agg")',
            "rc-refgs-fd-p2-lite-final-results-analysis-2026-06-01.json",
            "rc-refgs-fd-p2-lite-final-main-summary-2026-06-01.csv",
            "rc-refgs-fd-p2-lite-final-ablation-summary-2026-06-01.csv",
            "rc-refgs-fd-p2-lite-final-tradeoff-summary-2026-06-01.csv",
            "table1_main_base_vs_rc_summary",
            "table2_rc_win_counts_by_metric",
            "table3_ablation_aggregate",
            "table4_tradeoff_summary",
            "fig1_rc_consistency_delta_by_scene",
            "fig2_rc_win_rates_by_metric",
            "fig3_consistency_quality_tradeoff_map",
            "fig4_ablation_aggregate_comparison",
            "fig5_scope_coverage_summary",
            "README.md",
            'dpi=300',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_generator_has_no_execution_path_for_experiment_commands(self):
        script = Path(
            "docs/superpowers/figures/fd-p2-lite/"
            "make_fd_p2_lite_publication_tables_figures.py"
        )
        self.assertTrue(script.exists(), f"{script} is missing")

        source = script.read_text()
        for snippet in ["subprocess", "os.system", "Popen", "check_call", "check_output"]:
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
