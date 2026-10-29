class ScientificSpeechNormalizer {
  const ScientificSpeechNormalizer();
  String normalize(String value) {
    var text=value
      .replaceAll(RegExp(r'```[\\s\\S]*?```'), ' ')
      .replaceAll(RegExp(r'[#*_>`~-]'), ' ')
      .replaceAll('→', ' donne ')
      .replaceAll('↔', ' en équilibre avec ')
      .replaceAll('≈', ' environ ')
      .replaceAll('≠', ' différent de ')
      .replaceAll('≤', ' inférieur ou égal à ')
      .replaceAll('≥', ' supérieur ou égal à ')
      .replaceAll('°C', ' degrés Celsius ')
      .replaceAll('%', ' pour cent ')
      .replaceAll('μ', ' micro ')
      .replaceAll('Δ', ' delta ');
    text=text.replaceAllMapped(RegExp(r'([0-9])²'),(m)=>'${m.group(1)} au carré');
    text=text.replaceAllMapped(RegExp(r'([0-9])³'),(m)=>'${m.group(1)} au cube');
    return text.replaceAll(RegExp(r'\\s+'),' ').trim();
  }
}
