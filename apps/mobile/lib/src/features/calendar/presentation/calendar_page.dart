import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import 'package:go_router/go_router.dart';
import '../../../core/di/providers.dart';
import '../../study_plan/domain/study_plan.dart';

class CalendarPage extends ConsumerWidget {
  const CalendarPage({super.key});
  @override Widget build(BuildContext context,WidgetRef ref){
    final events=ref.watch(upcomingEventsProvider); final timetable=ref.watch(timetableProvider);
    return Scaffold(
      appBar:AppBar(title:const Text('Calendrier'),actions:[IconButton(tooltip:'Ajouter une échéance',onPressed:()=>_addEvent(context,ref),icon:const Icon(Icons.add_rounded))]),
      body:ListView(padding:const EdgeInsets.fromLTRB(18,8,18,120),children:[
        _ImportCard(onPressed:()=>context.push('/calendar/import')),
        const SizedBox(height:18),
        Text('Prochaines échéances',style:Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:10),
        events.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>_LoadError(message:'Impossible de charger les échéances.',onRetry:()=>ref.invalidate(upcomingEventsProvider)),data:(rows)=>rows.isEmpty?const _Empty(text:'Ajoute une interrogation, un examen ou un travail à remettre.'):Column(children:rows.take(8).map((e)=>_EventTile(event:e)).toList())),
        const SizedBox(height:22),
        Row(children:[Expanded(child:Text('Horaire hebdomadaire',style:Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight:FontWeight.w900))),IconButton(onPressed:()=>_addCourse(context,ref),icon:const Icon(Icons.add_circle_outline_rounded))]),
        const SizedBox(height:10),
        timetable.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>_LoadError(message:'Impossible de charger l’horaire.',onRetry:()=>ref.invalidate(timetableProvider)),data:(rows)=>rows.isEmpty?const _Empty(text:'Ajoute ton horaire ou importe-le depuis une photo/PDF.'):Column(children:rows.map((e)=>_TimetableTile(entry:e)).toList())),
      ]),
    );
  }

  Future<void> _addEvent(BuildContext context,WidgetRef ref) async {
    final title = TextEditingController();
    var date = DateTime.now().add(const Duration(days: 1));
    var kind = AcademicEventKind.interrogation;
    var saving = false;
    try {
      await showDialog<void>(context: context, builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Text('Nouvelle échéance'),
          content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: title, enabled: !saving, decoration: const InputDecoration(labelText: 'Titre')),
            DropdownButtonFormField<AcademicEventKind>(value: kind,
              items: AcademicEventKind.values.where((e) => e != AcademicEventKind.course)
                  .map((e) => DropdownMenuItem(value: e, child: Text(e.name))).toList(),
              onChanged: saving ? null : (v) { if (v != null) setDialogState(() => kind = v); },
              decoration: const InputDecoration(labelText: 'Type')),
            ListTile(title: Text('${date.day}/${date.month}/${date.year} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}'),
              trailing: const Icon(Icons.edit_calendar_rounded),
              onTap: saving ? null : () async {
                final d = await showDatePicker(context: dialogContext,
                  firstDate: DateTime.now().subtract(const Duration(days: 1)),
                  lastDate: DateTime.now().add(const Duration(days: 730)), initialDate: date);
                if (d != null && dialogContext.mounted) setDialogState(() => date = DateTime(d.year, d.month, d.day, 9));
              }),
          ])),
          actions: [
            TextButton(onPressed: saving ? null : () => Navigator.pop(dialogContext), child: const Text('Annuler')),
            FilledButton(onPressed: saving ? null : () async {
              if (title.text.trim().isEmpty) { _notice(dialogContext, 'Le titre est obligatoire.'); return; }
              setDialogState(() => saving = true);
              try {
                await ref.read(studyPlanRepositoryProvider).saveEvent(AcademicEvent(
                  id: const Uuid().v4(), title: title.text.trim(), kind: kind, startsAt: date));
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } catch (_) {
                if (dialogContext.mounted) {
                  setDialogState(() => saving = false);
                  _notice(dialogContext, 'Échec de l’enregistrement. Les informations sont conservées. Réessaie.');
                }
              }
            }, child: saving ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Enregistrer')),
          ],
        ),
      ));
    } finally { title.dispose(); }
  }

  Future<void> _addCourse(BuildContext context,WidgetRef ref) async {
    final title = TextEditingController();
    final startInput = TextEditingController(text: '08:00');
    final endInput = TextEditingController(text: '09:00');
    var weekday = DateTime.monday;
    var saving = false;
    try {
      await showDialog<void>(context: context, builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Text('Ajouter un cours à l’horaire'),
          content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: title, enabled: !saving, decoration: const InputDecoration(labelText: 'Cours')),
            DropdownButtonFormField<int>(value: weekday,
              items: List.generate(6, (i) => DropdownMenuItem(value: i + 1, child: Text(['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'][i]))),
              onChanged: saving ? null : (v) { if (v != null) setDialogState(() => weekday = v); },
              decoration: const InputDecoration(labelText: 'Jour')),
            Row(children: [
              Expanded(child: TextField(controller: startInput, enabled: !saving, decoration: const InputDecoration(labelText: 'Début (HH:MM)'))),
              const SizedBox(width: 10),
              Expanded(child: TextField(controller: endInput, enabled: !saving, decoration: const InputDecoration(labelText: 'Fin (HH:MM)'))),
            ]),
          ])),
          actions: [
            TextButton(onPressed: saving ? null : () => Navigator.pop(dialogContext), child: const Text('Annuler')),
            FilledButton(onPressed: saving ? null : () async {
              final start = _parse(startInput.text, -1);
              final end = _parse(endInput.text, -1);
              if (title.text.trim().isEmpty || start < 0 || end <= start || end > 1440) {
                _notice(dialogContext, 'Vérifie le cours et les horaires (HH:MM, début avant fin).'); return;
              }
              setDialogState(() => saving = true);
              try {
                await ref.read(studyPlanRepositoryProvider).saveTimetableEntry(TimetableEntry(
                  id: const Uuid().v4(), title: title.text.trim(), weekday: weekday, startMinute: start, endMinute: end));
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } catch (_) {
                if (dialogContext.mounted) {
                  setDialogState(() => saving = false);
                  _notice(dialogContext, 'Échec de l’enregistrement. Les informations sont conservées. Réessaie.');
                }
              }
            }, child: saving ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Ajouter')),
          ],
        ),
      ));
    } finally { title.dispose(); startInput.dispose(); endInput.dispose(); }
  }
  void _notice(BuildContext context,String message){if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(message)));}
  int _parse(String v,int fallback){final p=v.split(':');if(p.length!=2)return fallback;final h=int.tryParse(p[0]);final m=int.tryParse(p[1]);if(h==null||m==null||h<0||h>23||m<0||m>59)return -1;return h*60+m;}
}

class _ImportCard extends StatelessWidget{const _ImportCard({required this.onPressed});final VoidCallback onPressed;@override Widget build(BuildContext context)=>Card(child:ListTile(contentPadding:const EdgeInsets.all(16),leading:const CircleAvatar(child:Icon(Icons.document_scanner_rounded)),title:const Text('Importer mon horaire',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:const Text('Photo ou PDF → OCR → vérification → calendrier'),trailing:FilledButton.tonal(onPressed:onPressed,child:const Text('Importer'))));}
class _EventTile extends StatelessWidget{const _EventTile({required this.event});final AcademicEvent event;@override Widget build(BuildContext context){final d=event.startsAt;return Padding(padding:const EdgeInsets.only(bottom:10),child:Card(child:ListTile(contentPadding:const EdgeInsets.all(14),leading:SizedBox(width:46,child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Text('${d.day}'.padLeft(2,'0'),style:const TextStyle(fontSize:20,fontWeight:FontWeight.w900)),Text('${d.month}/${d.year%100}',style:Theme.of(context).textTheme.labelSmall)])),title:Text(event.title,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${event.kind.name} · ${d.hour.toString().padLeft(2,'0')}:${d.minute.toString().padLeft(2,'0')}'),trailing:const Icon(Icons.chevron_right_rounded))));}}
class _TimetableTile extends StatelessWidget{const _TimetableTile({required this.entry});final TimetableEntry entry;@override Widget build(BuildContext context){String hm(int m)=>'${(m~/60).toString().padLeft(2,'0')}:${(m%60).toString().padLeft(2,'0')}';final days=['','Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];return Padding(padding:const EdgeInsets.only(bottom:8),child:Card(child:ListTile(leading:CircleAvatar(child:Text(days[entry.weekday])),title:Text(entry.title,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${hm(entry.startMinute)} – ${hm(entry.endMinute)}${entry.location==null?'':' · ${entry.location}'}'))));}}
class _Empty extends StatelessWidget{const _Empty({required this.text});final String text;@override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(18),child:Text(text,textAlign:TextAlign.center)));}

class _LoadError extends StatelessWidget {const _LoadError({required this.message,required this.onRetry});final String message;final VoidCallback onRetry;@override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(children:[Text(message),TextButton.icon(onPressed:onRetry,icon:const Icon(Icons.refresh),label:const Text('Réessayer'))])));}
