import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/tokens.dart';
import '../../academic_profile/domain/academic_profile.dart';

class OnboardingPage extends ConsumerStatefulWidget {
  const OnboardingPage({super.key});

  @override
  ConsumerState<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends ConsumerState<OnboardingPage> {
  final _formKey = GlobalKey<FormState>();
  final _faculty = TextEditingController();
  final _program = TextEditingController();
  final _level = TextEditingController();
  final _semester = TextEditingController();
  final _institution = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _faculty.dispose();
    _program.dispose();
    _level.dispose();
    _semester.dispose();
    _institution.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                const SizedBox(height: 16),
                Icon(Icons.auto_awesome_rounded, size: 56, color: Theme.of(context).colorScheme.primary),
                const SizedBox(height: 20),
                Text('Configure ton parcours', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                Text('EduNova utilisera ton parcours pour organiser tes cours et tes priorités. Ton université reste facultative.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge),
                const SizedBox(height: EduNovaSpace.xl),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          _field(_faculty, 'Faculté / domaine', Icons.account_balance_rounded),
                          const SizedBox(height: 12),
                          _field(_program, 'Filière / programme', Icons.hub_rounded),
                          const SizedBox(height: 12),
                          Row(children: [
                            Expanded(child: _field(_level, 'Niveau', Icons.stairs_rounded)),
                            const SizedBox(width: 12),
                            Expanded(child: _field(_semester, 'Semestre', Icons.calendar_view_month_rounded)),
                          ]),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _institution,
                            decoration: const InputDecoration(prefixIcon: Icon(Icons.location_city_rounded), labelText: 'Université / établissement (facultatif)'),
                          ),
                          const SizedBox(height: 20),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: _saving ? null : _save,
                              icon: _saving ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_forward_rounded),
                              label: const Text('Continuer'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _field(TextEditingController controller, String label, IconData icon) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(prefixIcon: Icon(icon), labelText: label),
      validator: (value) => value == null || value.trim().isEmpty ? 'Champ requis' : null,
    );
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final profile = AcademicProfile(
      id: const Uuid().v4(),
      faculty: _faculty.text.trim(),
      program: _program.text.trim(),
      level: _level.text.trim(),
      semester: _semester.text.trim(),
      institution: _institution.text.trim().isEmpty ? null : _institution.text.trim(),
      updatedAt: DateTime.now().toUtc(),
    );
    await ref.read(academicProfileRepositoryProvider).save(profile);
    if (!mounted) return;
    context.go('/home');
  }
}
