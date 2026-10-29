import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/tokens.dart';
import '../../../shared/presentation/widgets/premium_surface.dart';
import '../application/scientific_speech_normalizer.dart';
import '../domain/audio.dart';

class AudioSummaryPage extends ConsumerStatefulWidget {
  const AudioSummaryPage({super.key, required this.courseId});
  final String courseId;
  @override ConsumerState<AudioSummaryPage> createState() => _AudioSummaryPageState();
}

class _AudioSummaryPageState extends ConsumerState<AudioSummaryPage> {
  bool _playing = false;
  bool _showTranscript = false;
  int _offset = 0;
  int _lastPersistedOffset = 0;
  double _rate = 1.0;
  String? _restoredPlaybackId;

  String _plain(String v) => v.replaceAll(RegExp(r'[#*_>`~-]'), ' ').replaceAll(RegExp(r'\s+'), ' ').trim();

  @override
  Widget build(BuildContext context) {
    final summariesAsync = ref.watch(courseSummariesProvider(widget.courseId));
    final summaries = summariesAsync.valueOrNull ?? const [];
    if (summariesAsync.isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Résumé audio')),
        body: const EduNovaPageBody(maxWidth: 760, child: PremiumPanel(child: Column(children: [SkeletonLine(width: 180, height: 20), SizedBox(height: 18), SkeletonLine(height: 180), SizedBox(height: 16), SkeletonLine(height: 52)]))),
      );
    }
    if (summariesAsync.hasError) {
      return Scaffold(
        appBar: AppBar(title: const Text('Résumé audio')),
        body: const EduNovaPageBody(maxWidth: 760, child: EmptyStateCard(icon: Icons.error_outline_rounded, title: 'Audio indisponible', message: 'Le résumé n’a pas pu être chargé. Tes autres contenus restent disponibles.')),
      );
    }
    if (summaries.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Résumé audio')),
        body: const EduNovaPageBody(maxWidth: 760, child: EmptyStateCard(icon: Icons.headphones_outlined, title: 'Aucun résumé audio', message: 'Ce cours n’a pas encore de résumé compatible avec la lecture audio.')),
      );
    }

    final summary = summaries.first;
    final raw = _plain(summary.bodyMarkdown);
    final text = const ScientificSpeechNormalizer().normalize(raw);
    final playbackId = 'summary:${summary.id}';
    final entitlement = ref.watch(entitlementProvider).valueOrNull;
    final premium = entitlement?.isPremiumOffline(DateTime.now()) ?? false;
    final spokenText = premium ? text : (text.length > 700 ? text.substring(0, 700) : text);
    if (_offset > spokenText.length) _offset = 0;

    final saved = ref.watch(audioPlaybackProvider(playbackId)).valueOrNull;
    final bookmarks = ref.watch(audioBookmarksProvider(playbackId)).valueOrNull ?? const [];
    if (saved != null && _restoredPlaybackId != playbackId) {
      _restoredPlaybackId = playbackId;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        setState(() {
          _offset = saved.characterOffset.clamp(0, spokenText.length).toInt();
          _lastPersistedOffset = _offset;
          _rate = saved.speechRate.clamp(.75, 2.0).toDouble();
        });
      });
    }

    final progress = spokenText.isEmpty ? 0.0 : (_offset / spokenText.length).clamp(0, 1).toDouble();
    final totalSeconds = math.max(60, summary.estimatedMinutes * 60);
    final elapsedSeconds = (totalSeconds * progress).round();
    final remainingSeconds = math.max(0, totalSeconds - elapsedSeconds);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Résumé audio'),
        actions: [
          IconButton(
            tooltip: 'Historique de l’assistant',
            onPressed: () => context.push('/assistant/history'),
            icon: const Icon(Icons.history_rounded),
          ),
        ],
      ),
      body: EduNovaPageBody(
        maxWidth: 820,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          _AudioHero(title: summary.title, premium: premium, playing: _playing, rate: _rate),
          const SizedBox(height: 14),
          if (!premium) ...[
            PremiumPanel(
              emphasis: true,
              child: Row(children: [
                Container(width: 48, height: 48, decoration: BoxDecoration(color: scheme.primaryContainer, borderRadius: BorderRadius.circular(16)), child: Icon(Icons.lock_outline_rounded, color: scheme.primary)),
                const SizedBox(width: 14),
                const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Aperçu audio gratuit', style: TextStyle(fontWeight: FontWeight.w900)), SizedBox(height: 3), Text('Passe Premium pour écouter le résumé complet, hors connexion.')])),
                TextButton(onPressed: () => context.push('/premium'), child: const Text('Premium')),
              ]),
            ),
            const SizedBox(height: 14),
          ],
          PremiumPanel(
            child: Column(children: [
              Semantics(
                label: 'Progression audio ${(progress * 100).round()} pour cent',
                child: Slider(
                  value: progress,
                  onChanged: spokenText.isEmpty ? null : (v) => setState(() => _offset = (spokenText.length * v).round().clamp(0, spokenText.length).toInt()),
                  onChangeEnd: (_) => _persist(playbackId, summary.id, summary.title),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 5),
                child: Row(children: [
                  Text(_formatDuration(elapsedSeconds), style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
                  const Spacer(),
                  Text('-${_formatDuration(remainingSeconds)}', style: TextStyle(color: scheme.onSurfaceVariant, fontWeight: FontWeight.w700)),
                ]),
              ),
              const SizedBox(height: 10),
              Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                IconButton.filledTonal(
                  tooltip: 'Reculer environ 10 secondes',
                  onPressed: () => _seek(spokenText.length, -_skipChars()),
                  icon: const Icon(Icons.replay_10_rounded),
                ),
                const SizedBox(width: 18),
                Semantics(
                  button: true,
                  label: _playing ? 'Mettre en pause' : 'Lire le résumé',
                  child: SizedBox(
                    width: 72,
                    height: 72,
                    child: FilledButton(
                      style: FilledButton.styleFrom(shape: const CircleBorder(), padding: EdgeInsets.zero),
                      onPressed: () => _togglePlayback(spokenText, playbackId, summary.id, summary.title, premium),
                      child: Icon(_playing ? Icons.pause_rounded : Icons.play_arrow_rounded, size: 38),
                    ),
                  ),
                ),
                const SizedBox(width: 18),
                IconButton.filledTonal(
                  tooltip: 'Avancer environ 10 secondes',
                  onPressed: () => _seek(spokenText.length, _skipChars()),
                  icon: const Icon(Icons.forward_10_rounded),
                ),
              ]),
              const SizedBox(height: 18),
              Wrap(alignment: WrapAlignment.center, spacing: 8, runSpacing: 8, children: [
                StatusPill(icon: Icons.speed_rounded, label: '${_rateLabel(_rate)}×'),
                const StatusPill(icon: Icons.cloud_off_rounded, label: 'Voix locale'),
                StatusPill(icon: premium ? Icons.workspace_premium_rounded : Icons.visibility_outlined, label: premium ? 'Audio complet' : 'Aperçu'),
              ]),
              const SizedBox(height: 14),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SegmentedButton<double>(
                  segments: const [
                    ButtonSegment(value: .75, label: Text('0,75×')),
                    ButtonSegment(value: 1.0, label: Text('1×')),
                    ButtonSegment(value: 1.25, label: Text('1,25×')),
                    ButtonSegment(value: 1.5, label: Text('1,5×')),
                    ButtonSegment(value: 2.0, label: Text('2×')),
                  ],
                  selected: {_rate},
                  onSelectionChanged: (v) => _changeRate(v.first, spokenText, playbackId, summary.id, summary.title, premium),
                ),
              ),
            ]),
          ),
          const SizedBox(height: 14),
          PremiumPanel(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(child: Text('Mes repères audio', style: Theme.of(context).textTheme.titleMedium)),
                FilledButton.tonalIcon(onPressed: () => _addBookmark(playbackId), icon: const Icon(Icons.bookmark_add_outlined), label: const Text('Ajouter')),
              ]),
              const SizedBox(height: 10),
              if (bookmarks.isEmpty)
                Text('Ajoute un repère sur une définition, une formule ou un passage à réécouter.', style: TextStyle(color: scheme.onSurfaceVariant))
              else
                Wrap(spacing: 8, runSpacing: 8, children: bookmarks.map((b) {
                  final p = spokenText.isEmpty ? 0 : ((b.characterOffset / spokenText.length) * 100).round().clamp(0, 100);
                  return ActionChip(
                    avatar: const Icon(Icons.bookmark_rounded, size: 18),
                    label: Text('${b.label ?? 'Repère'} · $p %'),
                    onPressed: () => setState(() => _offset = b.characterOffset.clamp(0, spokenText.length).toInt()),
                  );
                }).toList()),
            ]),
          ),
          const SizedBox(height: 14),
          PremiumPanel(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(child: Text('Texte du résumé', style: Theme.of(context).textTheme.titleMedium)),
                TextButton.icon(
                  onPressed: () => setState(() => _showTranscript = !_showTranscript),
                  icon: Icon(_showTranscript ? Icons.expand_less_rounded : Icons.expand_more_rounded),
                  label: Text(_showTranscript ? 'Réduire' : 'Afficher'),
                ),
              ]),
              AnimatedCrossFade(
                firstChild: Text(spokenText, maxLines: 5, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.55)),
                secondChild: Text(spokenText, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.62)),
                crossFadeState: _showTranscript ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                duration: MediaQuery.maybeOf(context)?.disableAnimations == true ? Duration.zero : EduNovaMotion.standard,
              ),
            ]),
          ),
        ]),
      ),
    );
  }

  int _skipChars() => (130 * _rate).round().clamp(80, 280);
  void _seek(int length, int delta) => setState(() => _offset = (_offset + delta).clamp(0, length).toInt());

  Future<void> _changeRate(double rate, String text, String playbackId, String? summaryId, String title, bool premium) async {
    final wasPlaying = _playing;
    final narrator = ref.read(ttsNarratorProvider);
    if (wasPlaying) await narrator.stop();
    setState(() { _rate = rate; _playing = false; });
    await _persist(playbackId, summaryId, title);
    if (wasPlaying) await _startPlayback(text, playbackId, summaryId, title, premium);
  }

  Future<void> _togglePlayback(String text, String playbackId, String? summaryId, String title, bool premium) async {
    final narrator = ref.read(ttsNarratorProvider);
    if (_playing) {
      await narrator.pause();
      if (mounted) setState(() => _playing = false);
      await _persist(playbackId, summaryId, title);
      return;
    }
    await _startPlayback(text, playbackId, summaryId, title, premium);
  }

  Future<void> _startPlayback(String text, String playbackId, String? summaryId, String title, bool premium) async {
    final narrator = ref.read(ttsNarratorProvider);
    await narrator.speak(
      text,
      startOffset: _offset,
      rate: _rate,
      onProgress: (_, end) {
        if (!mounted) return;
        setState(() => _offset = end.clamp(0, text.length).toInt());
        if ((_offset - _lastPersistedOffset).abs() >= 180) {
          _lastPersistedOffset = _offset;
          _persist(playbackId, summaryId, title);
        }
      },
      onComplete: () {
        if (!mounted) return;
        setState(() { _playing = false; _offset = text.length; });
        ref.read(audioRepositoryProvider).savePlayback(AudioPlaybackState(
          id: playbackId,
          courseId: widget.courseId,
          summaryId: summaryId,
          title: title,
          characterOffset: text.length,
          speechRate: _rate,
          completed: premium,
          lastPlayedAt: DateTime.now(),
        ));
      },
    );
    if (mounted) setState(() => _playing = true);
    await _persist(playbackId, summaryId, title);
  }

  Future<void> _persist(String playbackId, String? summaryId, String title) => ref.read(audioRepositoryProvider).savePlayback(AudioPlaybackState(
        id: playbackId,
        courseId: widget.courseId,
        summaryId: summaryId,
        title: title,
        characterOffset: _offset,
        speechRate: _rate,
        lastPlayedAt: DateTime.now(),
      ));

  Future<void> _addBookmark(String playbackId) async {
    await ref.read(audioRepositoryProvider).addBookmark(AudioBookmark(
      id: const Uuid().v4(),
      playbackId: playbackId,
      characterOffset: _offset,
      label: 'Repère audio',
      createdAt: DateTime.now(),
    ));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Repère audio enregistré.')));
  }

  String _formatDuration(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '$m:${s.toString().padLeft(2, '0')}';
  }

  String _rateLabel(double value) => value == value.roundToDouble() ? value.toStringAsFixed(0) : value.toStringAsFixed(2).replaceFirst(RegExp(r'0$'), '');

  @override
  void dispose() {
    ref.read(ttsNarratorProvider).stop();
    super.dispose();
  }
}

class _AudioHero extends StatelessWidget {
  const _AudioHero({required this.title, required this.premium, required this.playing, required this.rate});
  final String title; final bool premium; final bool playing; final double rate;
  @override Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [scheme.primary, Color.lerp(scheme.primary, EduNovaColors.secondary, .42)!]),
        borderRadius: BorderRadius.circular(EduNovaRadius.xl),
        boxShadow: [BoxShadow(color: scheme.primary.withValues(alpha: .20), blurRadius: 30, offset: const Offset(0, 12))],
      ),
      child: Row(children: [
        Container(
          width: 82,
          height: 82,
          decoration: BoxDecoration(color: scheme.onPrimary.withValues(alpha: .15), borderRadius: BorderRadius.circular(26)),
          child: AnimatedSwitcher(
            duration: MediaQuery.maybeOf(context)?.disableAnimations == true ? Duration.zero : EduNovaMotion.standard,
            child: Icon(playing ? Icons.graphic_eq_rounded : Icons.headphones_rounded, key: ValueKey(playing), size: 38, color: scheme.onPrimary),
          ),
        ),
        const SizedBox(width: 18),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(premium ? 'RÉSUMÉ AUDIO PREMIUM' : 'APERÇU AUDIO', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .78), fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: .55)),
          const SizedBox(height: 7),
          Text(title, maxLines: 3, overflow: TextOverflow.ellipsis, style: TextStyle(color: scheme.onPrimary, fontSize: 23, height: 1.12, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text('Voix locale · ${rate.toStringAsFixed(rate == 1 ? 0 : 2).replaceFirst(RegExp(r'0$'), '')}× · hors connexion', style: TextStyle(color: scheme.onPrimary.withValues(alpha: .88), fontWeight: FontWeight.w600)),
        ])),
      ]),
    );
  }
}
