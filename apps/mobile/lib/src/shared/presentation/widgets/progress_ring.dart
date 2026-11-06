import 'package:flutter/material.dart';

class ProgressRing extends StatelessWidget {
  const ProgressRing({super.key, required this.value, this.size = 72});

  final double value;
  final double size;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SizedBox.square(
      dimension: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: value,
            strokeWidth: 7,
            strokeCap: StrokeCap.round,
            backgroundColor: scheme.surfaceContainerHighest,
          ),
          Text('${(value * 100).round()}%', style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}
