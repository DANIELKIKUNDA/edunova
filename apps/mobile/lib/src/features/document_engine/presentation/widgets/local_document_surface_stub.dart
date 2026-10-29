import 'package:flutter/material.dart';
import '../../../content/domain/personal_document.dart';

class LocalDocumentSurface extends StatelessWidget {
  const LocalDocumentSurface({super.key, required this.document, required this.initialPage, required this.onPageChanged});
  final PersonalDocument document;
  final int initialPage;
  final void Function(int page, int totalPages) onPageChanged;

  @override
  Widget build(BuildContext context) => const Center(child: Padding(
    padding: EdgeInsets.all(28),
    child: Text('Le stockage binaire PWA/OPFS et le rendu Web seront certifiés dans le lot Web/offline dédié.', textAlign: TextAlign.center),
  ));
}
