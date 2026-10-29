import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';

import '../../../content/domain/personal_document.dart';

class LocalDocumentSurface extends StatefulWidget {
  const LocalDocumentSurface({super.key, required this.document, required this.initialPage, required this.onPageChanged});
  final PersonalDocument document;
  final int initialPage;
  final void Function(int page, int totalPages) onPageChanged;

  @override
  State<LocalDocumentSurface> createState() => _LocalDocumentSurfaceState();
}

class _LocalDocumentSurfaceState extends State<LocalDocumentSurface> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && widget.document.isImage) widget.onPageChanged(1, 1);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (widget.document.isImage) {
      return InteractiveViewer(
        minScale: .8,
        maxScale: 5,
        child: Center(child: Image.file(File(widget.document.localUri), fit: BoxFit.contain, errorBuilder: (_, __, ___) => const _ReadError())),
      );
    }
    if (widget.document.mimeType == 'application/pdf') {
      return PdfViewer.file(widget.document.localUri);
    }
    return const _ReadError();
  }
}

class _ReadError extends StatelessWidget {
  const _ReadError();
  @override
  Widget build(BuildContext context) => const Center(child: Padding(
    padding: EdgeInsets.all(28),
    child: Text('Ce document ne peut pas être affiché sur cet appareil.', textAlign: TextAlign.center),
  ));
}
