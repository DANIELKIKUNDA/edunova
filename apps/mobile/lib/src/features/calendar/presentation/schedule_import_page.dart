import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../core/di/providers.dart';
import '../../study_plan/application/schedule_text_parser.dart';

class ScheduleImportPage extends ConsumerStatefulWidget {
  const ScheduleImportPage({super.key});
  @override ConsumerState<ScheduleImportPage> createState()=>_ScheduleImportPageState();
}

class _ScheduleImportPageState extends ConsumerState<ScheduleImportPage>{
  final _text=TextEditingController();
  List<ParsedTimetableRow> _rows=const [];
  bool _saving=false;
  @override void dispose(){_text.dispose();super.dispose();}
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Importer mon horaire')),
    body:ListView(padding:const EdgeInsets.fromLTRB(18,12,18,32),children:[
      Card(child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Row(children:[CircleAvatar(child:Icon(Icons.document_scanner_rounded)),SizedBox(width:12),Expanded(child:Text('Photo/PDF → OCR → vérification',style:TextStyle(fontWeight:FontWeight.w900,fontSize:17)))]),
        const SizedBox(height:10),
        const Text('Le moteur OCR du LOT 2 fournit le texte. EduNova ne publie jamais l’horaire détecté automatiquement : tu le vérifies avant l’enregistrement.'),
      ]))),
      const SizedBox(height:14),
      TextField(controller:_text,minLines:7,maxLines:14,decoration:const InputDecoration(labelText:'Texte OCR / horaire',hintText:'Lundi 08:00-10:00 Anatomie\nMercredi 14h30-16h00 Chimie',border:OutlineInputBorder())),
      const SizedBox(height:12),
      FilledButton.icon(onPressed:_parse,icon:const Icon(Icons.auto_fix_high_rounded),label:const Text('Analyser et vérifier')),
      if(_rows.isNotEmpty)...[
        const SizedBox(height:20),Text('${_rows.length} séance(s) détectée(s)',style:Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:10),
        ..._rows.map((r)=>Card(child:ListTile(leading:CircleAvatar(child:Text(_day(r.weekday))),title:Text(r.title,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${_hm(r.startMinute)} – ${_hm(r.endMinute)} · confiance ${(r.confidence*100).round()} %')))),
        const SizedBox(height:14),FilledButton.icon(onPressed:_saving?null:_save,icon:_saving?const SizedBox.square(dimension:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_circle_rounded),label:const Text('Valider cet horaire')),
      ]
    ]),
  );
  void _parse(){setState(()=>_rows=const ScheduleTextParser().parse(_text.text));if(_rows.isEmpty)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Aucune ligne fiable détectée. Vérifie le format ou l’OCR.')));}
  Future<void> _save() async {setState(()=>_saving=true);try{final repo=ref.read(studyPlanRepositoryProvider);for(final row in _rows){final entry=row.toEntry(const Uuid().v4());final conflicts=await repo.findTimetableConflicts(entry);if(conflicts.isNotEmpty&&mounted){final keep=await showDialog<bool>(context:context,builder:(c)=>AlertDialog(title:const Text('Conflit d’horaire'),content:Text('${entry.title} chevauche ${conflicts.first.title}. Enregistrer quand même ?'),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Non')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Oui'))]));if(keep!=true)continue;}await repo.saveTimetableEntry(entry);}if(mounted){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Horaire vérifié et enregistré.')));Navigator.pop(context);}}finally{if(mounted)setState(()=>_saving=false);}}
  String _day(int d)=>['','Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][d];
  String _hm(int m)=>'${(m~/60).toString().padLeft(2,'0')}:${(m%60).toString().padLeft(2,'0')}';
}
