import 'package:flutter/material.dart';

import '../../../core/theme/tokens.dart';

class EduNovaPageBody extends StatelessWidget {
  const EduNovaPageBody({
    super.key,
    required this.child,
    this.maxWidth = EduNovaLayout.maxContentWidth,
    this.padding = const EdgeInsets.fromLTRB(18, 8, 18, 120),
  });

  final Widget child;
  final double maxWidth;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

class PremiumPanel extends StatelessWidget {
  const PremiumPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.emphasis = false,
  });
  final Widget child;
  final EdgeInsets padding;
  final bool emphasis;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: emphasis ? scheme.primaryContainer.withValues(alpha: 0.36) : scheme.surface,
        borderRadius: BorderRadius.circular(EduNovaRadius.lg),
        border: Border.all(color: emphasis ? scheme.primary.withValues(alpha: 0.22) : scheme.outlineVariant.withValues(alpha: 0.48)),
        boxShadow: [
          BoxShadow(
            blurRadius: emphasis ? 26 : 18,
            offset: const Offset(0, 8),
            color: scheme.shadow.withValues(alpha: emphasis ? 0.08 : 0.045),
          ),
        ],
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.icon, required this.label, this.tone});
  final IconData icon;
  final String label;
  final Color? tone;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final color = tone ?? scheme.primary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(EduNovaRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.16)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Flexible(child: Text(label, overflow: TextOverflow.ellipsis, style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 12))),
      ]),
    );
  }
}

class EmptyStateCard extends StatelessWidget {
  const EmptyStateCard({super.key, required this.icon, required this.title, required this.message, this.action});
  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return PremiumPanel(
      child: Column(children: [
        Container(
          width: 58,
          height: 58,
          decoration: BoxDecoration(color: scheme.primaryContainer.withValues(alpha: 0.65), shape: BoxShape.circle),
          child: Icon(icon, color: scheme.primary, size: 28),
        ),
        const SizedBox(height: 14),
        Text(title, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        Text(message, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant)),
        if (action != null) ...[const SizedBox(height: 16), action!],
      ]),
    );
  }
}

class SkeletonLine extends StatefulWidget {
  const SkeletonLine({super.key, this.height = 14, this.width});
  final double height;
  final double? width;
  @override State<SkeletonLine> createState() => _SkeletonLineState();
}

class _SkeletonLineState extends State<SkeletonLine> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  @override void initState() { super.initState(); _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1100))..repeat(reverse: true); }
  @override void dispose() { _controller.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) {
    final disable = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final scheme = Theme.of(context).colorScheme;
    if (disable) return _box(scheme.outlineVariant.withValues(alpha: .35));
    return FadeTransition(opacity: Tween(begin: .45, end: .8).animate(_controller), child: _box(scheme.outlineVariant.withValues(alpha: .42)));
  }
  Widget _box(Color color) => Container(width: widget.width, height: widget.height, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(999)));
}
