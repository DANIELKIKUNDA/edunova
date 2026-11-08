import 'package:flutter/material.dart';

abstract final class EduNovaColors {
  static const primary = Color(0xFF5A5CE2);
  static const primaryDeep = Color(0xFF4143C8);
  static const secondary = Color(0xFF00AFA0);
  static const accent = Color(0xFFFFB648);
  static const danger = Color(0xFFED5D6A);
  static const success = Color(0xFF1EAA75);
  static const info = Color(0xFF3B82F6);
  static const ink = Color(0xFF161927);
  static const mutedInk = Color(0xFF64697A);
  static const canvas = Color(0xFFF7F8FC);
  static const surfaceSoft = Color(0xFFF0F2F8);
  static const darkCanvas = Color(0xFF0E1118);
  static const darkSurface = Color(0xFF171B25);
  static const darkSurfaceSoft = Color(0xFF202636);
}

abstract final class EduNovaSpace {
  static const xxs = 2.0;
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
  static const xxxl = 48.0;
}

abstract final class EduNovaRadius {
  static const sm = 12.0;
  static const md = 18.0;
  static const lg = 24.0;
  static const xl = 30.0;
  static const pill = 999.0;
}

abstract final class EduNovaMotion {
  static const fast = Duration(milliseconds: 160);
  static const standard = Duration(milliseconds: 240);
  static const slow = Duration(milliseconds: 360);
  static const curve = Curves.easeOutCubic;
}

abstract final class EduNovaLayout {
  static const compactBreakpoint = 640.0;
  static const railBreakpoint = 920.0;
  static const extendedRailBreakpoint = 1200.0;
  static const maxContentWidth = 1180.0;
  static const readableWidth = 760.0;
}
