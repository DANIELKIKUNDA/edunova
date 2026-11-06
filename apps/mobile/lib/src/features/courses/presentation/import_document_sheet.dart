
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mime/mime.dart';

import '../../../core/di/providers.dart';
import '../../content/application/import_personal_document.dart';
import '../../content/application/local_document_store.dart';
import '../../content/domain/personal_document.dart';

class ImportDocumentSheet extends ConsumerStatefulWidget {
  const ImportDocumentSheet({super.key});

  @override
  ConsumerState<ImportDocumentSheet> createState() => _ImportDocumentSheetState();
}

class _ImportDocumentSheetState extends ConsumerState<ImportDocumentSheet> {
  final _title = TextEditingController();
  final _course = TextEditingController();
  final _imagePicker = ImagePicker();
  PersonalDocumentType _type = PersonalDocumentType.course;
  _SelectedDocument? _file;
  bool _saving = false;

  @override
  void dispose() {
    _title.dispose();
    _course.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 20 + bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Align(
              alignment: Alignment.center,
              child: Container(width: 42, height: 4, decoration: BoxDecoration(color: Theme.of(context).colorScheme.outlineVariant, borderRadius: BorderRadius.circular(99))),
            ),
            const SizedBox(height: 18),
            Text('Ajouter à ma bibliothèque', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            const Text('Le fichier personnel reste dans l’espace privé de l’application.'),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(child: OutlinedButton.icon(onPressed: _pickFile, icon: const Icon(Icons.upload_file_rounded), label: const Text('PDF / image'))),
                const SizedBox(width: 10),
                Expanded(child: OutlinedButton.icon(onPressed: _takePhoto, icon: const Icon(Icons.photo_camera_rounded), label: const Text('Photographier'))),
              ],
            ),
            if (_file != null) ...[
              const SizedBox(height: 10),
              Card(
                child: ListTile(
                  leading: Icon(_file!.mimeType.startsWith('image/') ? Icons.image_rounded : Icons.picture_as_pdf_rounded),
                  title: Text(_file!.name, maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${(_file!.size / 1024 / 1024).toStringAsFixed(2)} Mo'),
                  trailing: IconButton(onPressed: () => setState(() => _file = null), icon: const Icon(Icons.close_rounded)),
                ),
              ),
            ],
            const SizedBox(height: 14),
            TextField(controller: _title, decoration: const InputDecoration(labelText: 'Titre du document')),
            const SizedBox(height: 12),
            TextField(controller: _course, decoration: const InputDecoration(labelText: 'Matière / cours (facultatif)')),
            const SizedBox(height: 12),
            DropdownButtonFormField<PersonalDocumentType>(
              initialValue: _type,
              decoration: const InputDecoration(labelText: 'Type'),
              items: PersonalDocumentType.values.map((value) => DropdownMenuItem(value: value, child: Text(_label(value)))).toList(),
              onChanged: (value) => setState(() => _type = value ?? _type),
            ),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: _saving || _file == null ? null : _import,
              icon: _saving ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.lock_rounded),
              label: const Text('Enregistrer dans mon espace privé'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: false,
      withData: kIsWeb,
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png', 'webp'],
    );
    if (result == null || result.files.isEmpty) return;
    final picked = result.files.single;
    final mimeType = lookupMimeType(picked.name, headerBytes: picked.bytes) ?? 'application/octet-stream';
    _setSelection(
      _SelectedDocument(
        name: picked.name,
        mimeType: mimeType,
        size: picked.size,
        path: picked.path,
        bytes: picked.bytes,
      ),
    );
  }

  Future<void> _takePhoto() async {
    final photo = await _imagePicker.pickImage(source: ImageSource.camera, imageQuality: 92);
    if (photo == null) return;
    final bytes = kIsWeb ? await photo.readAsBytes() : null;
    final size = bytes?.length ?? await photo.length();
    _setSelection(
      _SelectedDocument(
        name: photo.name,
        mimeType: lookupMimeType(photo.name) ?? 'image/jpeg',
        size: size,
        path: kIsWeb ? null : photo.path,
        bytes: bytes,
      ),
    );
    if (_type == PersonalDocumentType.course) {
      setState(() => _type = PersonalDocumentType.interrogation);
    }
  }

  void _setSelection(_SelectedDocument file) {
    setState(() {
      _file = file;
      if (_title.text.trim().isEmpty) {
        _title.text = file.name.replaceFirst(RegExp(r'\.[^.]+$'), '');
      }
    });
  }

  Future<void> _import() async {
    final file = _file!;
    setState(() => _saving = true);
    try {
      final candidate = LocalDocumentCandidate(
        fileName: file.name,
        mimeType: file.mimeType,
        sizeBytes: file.size,
        sourcePath: file.path,
        bytes: file.bytes,
      );
      await ref.read(importPersonalDocumentProvider)(
            ImportPersonalDocumentCommand(
              candidate: candidate,
              title: _title.text.trim().isEmpty ? file.name : _title.text.trim(),
              type: _type,
              courseName: _course.text.trim(),
            ),
          );
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Document ajouté à ta bibliothèque privée.')));
    } on UnsupportedError catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.message?.toString() ?? error.toString())));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _label(PersonalDocumentType type) => switch (type) {
        PersonalDocumentType.course => 'Cours',
        PersonalDocumentType.interrogation => 'Interrogation',
        PersonalDocumentType.exam => 'Examen',
        PersonalDocumentType.exercise => 'Exercice',
        PersonalDocumentType.notes => 'Notes',
        PersonalDocumentType.other => 'Autre',
      };
}

class _SelectedDocument {
  const _SelectedDocument({
    required this.name,
    required this.mimeType,
    required this.size,
    this.path,
    this.bytes,
  });

  final String name;
  final String mimeType;
  final int size;
  final String? path;
  final Uint8List? bytes;
}
