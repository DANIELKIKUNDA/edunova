import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'editorial_api.dart';

class IngestionPage extends StatefulWidget {
  final EditorialApi api;
  const IngestionPage({super.key, required this.api});

  @override
  State<IngestionPage> createState() => _IngestionPageState();
}

class _IngestionPageState extends State<IngestionPage> {
  bool loading = true;
  String? error;
  Map<String, dynamic> dashboard = const {};
  List<dynamic> batches = const [];
  String role = 'reviewer';
  bool get canEdit => role == 'owner' || role == 'editor';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { loading = true; error = null; });
    try {
      final values = await Future.wait([
        widget.api.ingestionDashboard(),
        widget.api.ingestionBatches(),
        widget.api.me(),
      ]);
      if (!mounted) return;
      setState(() {
        dashboard = values[0] as Map<String, dynamic>;
        batches = values[1] as List<dynamic>;
        role = (values[2] as Map<String,dynamic>)['role']?.toString() ?? 'reviewer';
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { error = e.toString(); loading = false; });
    }
  }

  Future<void> _createBatch() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => const CreateBatchDialog(),
    );
    if (result == null) return;
    try {
      final batch = await widget.api.createIngestionBatch(result);
      if (!mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => IngestionBatchPage(api: widget.api, batchId: batch['id'] as String, canEdit: canEdit),
      ));
      _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Création impossible : $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.cloud_off_rounded, size: 42),
        const SizedBox(height: 12),
        Text('Impossible de charger la chaîne d’ingestion', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        FilledButton.icon(onPressed: _load, icon: const Icon(Icons.refresh_rounded), label: const Text('Réessayer')),
      ]));
    }
    final width = MediaQuery.sizeOf(context).width;
    final columns = width >= 1200 ? 4 : width >= 720 ? 2 : 1;
    final backlog = dashboard['backlog_jobs'] ?? 0;
    final dead = dashboard['dead_letter_jobs'] ?? 0;
    final oldest = dashboard['oldest_pending_seconds'];
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Ingestion industrielle', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text('Déposez des lots de PDF et scans. EduNova contrôle, OCRise, reprend les erreurs et crée des brouillons traçables dans le Studio.', style: Theme.of(context).textTheme.bodyMedium),
            ])),
            const SizedBox(width: 12),
            FilledButton.icon(onPressed: canEdit ? _createBatch : null, icon: const Icon(Icons.create_new_folder_rounded), label: const Text('Nouveau lot')),
          ]),
          const SizedBox(height: 22),
          GridView.count(
            crossAxisCount: columns,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: columns == 1 ? 4.3 : 2.8,
            children: [
              _MetricCard(icon: Icons.inventory_2_outlined, label: 'Lots récents', value: '${dashboard['batches'] ?? 0}'),
              _MetricCard(icon: Icons.pending_actions_rounded, label: 'Jobs en attente', value: '$backlog'),
              _MetricCard(icon: Icons.report_problem_outlined, label: 'Dead-letter', value: '$dead', danger: dead is int && dead > 0),
              _MetricCard(icon: Icons.timer_outlined, label: 'Plus ancien en attente', value: oldest == null ? '—' : _duration(oldest as int), danger: dashboard['sla_breached'] == true),
            ],
          ),
          const SizedBox(height: 24),
          Row(children: [
            Expanded(child: Text('Lots', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800))),
            IconButton(onPressed: _load, tooltip: 'Actualiser', icon: const Icon(Icons.refresh_rounded)),
          ]),
          const SizedBox(height: 8),
          if (batches.isEmpty)
            const _EmptyPanel()
          else
            ...batches.map((raw) {
              final b = raw as Map<String, dynamic>;
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  clipBehavior: Clip.antiAlias,
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                    leading: _StateAvatar(state: b['state']?.toString() ?? ''),
                    title: Text(b['name']?.toString() ?? 'Lot', style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${b['defaults']?['faculty_domain'] ?? ''} • ${b['defaults']?['program'] ?? ''} • ${b['defaults']?['level'] ?? ''}'),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () async {
                      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => IngestionBatchPage(api: widget.api, batchId: b['id'] as String, canEdit: canEdit)));
                      _load();
                    },
                  ),
                ),
              );
            }),
        ],
      ),
    );
  }

  static String _duration(int seconds) {
    if (seconds < 60) return '${seconds}s';
    if (seconds < 3600) return '${(seconds / 60).floor()} min';
    return '${(seconds / 3600).floor()} h';
  }
}

class IngestionBatchPage extends StatefulWidget {
  final EditorialApi api;
  final String batchId;
  final bool canEdit;
  const IngestionBatchPage({super.key, required this.api, required this.batchId, required this.canEdit});
  @override State<IngestionBatchPage> createState() => _IngestionBatchPageState();
}

class _IngestionBatchPageState extends State<IngestionBatchPage> {
  Map<String, dynamic>? data;
  bool busy = false;
  String? error;

  @override void initState(){super.initState();_load();}

  Future<void> _load() async {
    try {
      final v = await widget.api.ingestionBatch(widget.batchId);
      if (mounted) setState(() { data = v; error = null; });
    } catch (e) { if (mounted) setState(() => error = e.toString()); }
  }

  Future<void> _pickFiles() async {
    final batch = data?['batch'] as Map<String,dynamic>?;
    if (batch?['state'] != 'draft') return;
    final selection = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      withData: true,
      type: FileType.custom,
      allowedExtensions: const ['pdf','png','jpg','jpeg','webp'],
    );
    if (selection == null) return;
    setState(() => busy = true);
    var accepted = 0; var rejected = 0;
    for (final f in selection.files) {
      final Uint8List? bytes = f.bytes;
      if (bytes == null) { rejected++; continue; }
      try {
        final result = await widget.api.uploadIngestionFile(widget.batchId, f.name, bytes, 'application/octet-stream', idempotencyKey: 'studio-${widget.batchId}-${f.name}-${f.size}-${f.identifier ?? ''}');
        if (result['state'] == 'rejected') { rejected++; } else { accepted++; }
      } catch (_) { rejected++; }
    }
    if (mounted) {
      setState(() => busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$accepted accepté(s) • $rejected rejeté(s)')));
      _load();
    }
  }

  Future<void> _pickImageBundle() async {
    final batch=data?['batch'] as Map<String,dynamic>?; if(batch?['state']!='draft')return;
    final selection=await FilePicker.platform.pickFiles(allowMultiple:true,withData:true,type:FileType.custom,allowedExtensions:const ['png','jpg','jpeg','webp']);
    if(!mounted||selection==null||selection.files.isEmpty)return;
    final nameController=TextEditingController(text:'Interrogation scannée');
    final bundleName=await showDialog<String>(context:context,builder:(c)=>AlertDialog(title:const Text('Regrouper les photos'),content:TextField(controller:nameController,decoration:const InputDecoration(labelText:'Nom du document',helperText:'Les photos seront assemblées dans l’ordre sélectionné.')),actions:[TextButton(onPressed:()=>Navigator.pop(c),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(c,nameController.text.trim()),child:const Text('Assembler'))]));
    if(bundleName==null||bundleName.isEmpty)return;
    final entries=<MapEntry<String,List<int>>>[];
    for(final f in selection.files){if(f.bytes!=null)entries.add(MapEntry(f.name,f.bytes!));}
    if(entries.isEmpty)return;
    setState(()=>busy=true);
    try{await widget.api.uploadImageBundle(widget.batchId,bundleName,entries,idempotencyKey:'bundle-${widget.batchId}-${entries.map((e)=>e.key).join('|')}');if(mounted && context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('${entries.length} photo(s) regroupée(s) en un document')));await _load();}
    catch(e){if(mounted && context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Assemblage impossible : $e')));}
    finally{if(mounted)setState(()=>busy=false);}
  }

  Future<void> _start() async {
    setState(() => busy = true);
    try { await widget.api.startIngestionBatch(widget.batchId, priority: 70); await _load(); }
    catch(e){ if(mounted && context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Démarrage impossible : $e'))); }
    finally { if(mounted)setState(()=>busy=false); }
  }

  @override Widget build(BuildContext context){
    if(data==null&&error==null)return const Scaffold(body:Center(child:CircularProgressIndicator()));
    if(error!=null)return Scaffold(appBar:AppBar(),body:Center(child:FilledButton.icon(onPressed:_load,icon:const Icon(Icons.refresh_rounded),label:const Text('Réessayer'))));
    final batch=data!['batch'] as Map<String,dynamic>; final metrics=data!['metrics'] as Map<String,dynamic>; final docs=(data!['documents'] as List).cast<Map<String,dynamic>>(); final jobs=(data!['jobs'] as List).cast<Map<String,dynamic>>(); final results=(data!['results'] as List).cast<Map<String,dynamic>>();
    final draft=batch['state']=='draft';
    return Scaffold(
      appBar:AppBar(title:Text(batch['name']?.toString()??'Lot'),actions:[IconButton(onPressed:_load,icon:const Icon(Icons.refresh_rounded),tooltip:'Actualiser')]),
      body:ListView(padding:const EdgeInsets.all(20),children:[
        Card(child:Padding(padding:const EdgeInsets.all(18),child:Wrap(spacing:18,runSpacing:12,crossAxisAlignment:WrapCrossAlignment.center,children:[
          _StateAvatar(state:batch['state']?.toString()??''),
          _Mini(label:'Documents',value:'${metrics['total_documents']??0}'),_Mini(label:'Réussis',value:'${metrics['succeeded']??0}'),_Mini(label:'Rejetés',value:'${metrics['rejected']??0}'),_Mini(label:'Dead-letter',value:'${metrics['dead_letter']??0}'),
          if(batch['manifest_sha256']!=null)Tooltip(message:'Manifest figé : ${batch['manifest_sha256']}',child:const Chip(avatar:Icon(Icons.verified_outlined,size:18),label:Text('Manifest figé'))),
        ]))),
        const SizedBox(height:16),
        Wrap(spacing:10,runSpacing:10,children:[
          FilledButton.icon(onPressed:draft&&widget.canEdit&&!busy?_pickFiles:null,icon:const Icon(Icons.upload_file_rounded),label:Text(busy?'Traitement…':'Ajouter des fichiers')),
          OutlinedButton.icon(onPressed:draft&&widget.canEdit&&!busy?_pickImageBundle:null,icon:const Icon(Icons.photo_library_outlined),label:const Text('Regrouper des photos')),
          FilledButton.tonalIcon(onPressed:draft&&widget.canEdit&&docs.any((d)=>d['state']=='accepted')&&!busy?_start:null,icon:const Icon(Icons.play_arrow_rounded),label:const Text('Figer et traiter')),
          if(!draft)Chip(avatar:const Icon(Icons.lock_outline_rounded,size:18),label:Text('Lot ${batch['state']}')),
        ]),
        if(!draft&&docs.isNotEmpty)...[const SizedBox(height:14),LinearProgressIndicator(value:((metrics['succeeded']??0)+(metrics['dead_letter']??0)+(metrics['rejected']??0))/docs.length),const SizedBox(height:6),Text('${(metrics['succeeded']??0)} réussi(s) • ${(metrics['dead_letter']??0)} dead-letter • ${(metrics['rejected']??0)} rejeté(s)',style:Theme.of(context).textTheme.labelMedium)],
        const SizedBox(height:22),
        Text('Documents',style:Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w800)),
        const SizedBox(height:8),
        if(docs.isEmpty)const _EmptyPanel(message:'Ajoutez des PDF ou scans pour commencer.') else ...docs.map((d){
          final job=jobs.cast<Map<String,dynamic>?>().firstWhere((j)=>j?['document_id']==d['id'],orElse:()=>null);
          final result=results.cast<Map<String,dynamic>?>().firstWhere((r)=>r?['document_id']==d['id'],orElse:()=>null);
          return Card(child:ListTile(
            leading:_StateAvatar(state:d['state']?.toString()??''),
            title:Text(d['filename']?.toString()??'',style:const TextStyle(fontWeight:FontWeight.w700)),
            subtitle:Text(_documentSubtitle(d,job,result)),
            trailing:Wrap(spacing:4,crossAxisAlignment:WrapCrossAlignment.center,children:[
              if(result?['needs_human_verification']==true)const Tooltip(message:'Vérification humaine requise',child:Icon(Icons.verified_user_outlined,color:Colors.orange)),
              if(d['editorial_item_id']!=null)const Tooltip(message:'Brouillon Studio créé',child:Icon(Icons.fact_check_outlined)),
              if(job?['state']=='dead_letter')IconButton(tooltip:'Réessayer',icon:const Icon(Icons.replay_rounded),onPressed:()async{try{await widget.api.retryIngestionJob(job!['id'] as String);await _load();}catch(e){if(mounted && context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Retry impossible : $e')));}}),
            ]),
            onTap:d['state']=='succeeded'?()=>_showPreview(d):null,
          ));
        }),
      ]),
    );
  }

  String _documentSubtitle(Map<String,dynamic>d,Map<String,dynamic>?j,Map<String,dynamic>?r){
    final pieces=<String>[d['state']?.toString()??'']; if(d['page_count']!=null)pieces.add('${d['page_count']} page(s)'); if(d['rejection_code']!=null)pieces.add(d['rejection_code'].toString()); if(j?['attempt']!=null)pieces.add('tentative ${j!['attempt']}/${j['max_attempts']}'); if(r?['mean_ocr_confidence']!=null)pieces.add('OCR ${(((r!['mean_ocr_confidence'] as num)*100).round())}%'); return pieces.join(' • ');
  }

  Future<void> _showPreview(Map<String,dynamic>d)async{
    try{
      final preview=await widget.api.ingestionPreview(d['id'] as String,page:1); if(!mounted)return;
      showModalBottomSheet(context:context,isScrollControlled:true,builder:(c)=>DraggableScrollableSheet(expand:false,initialChildSize:.78,maxChildSize:.92,builder:(c,scroll)=>Padding(padding:const EdgeInsets.all(20),child:ListView(controller:scroll,children:[
        Text(d['filename'].toString(),style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
        Text('Aperçu OCR / extraction — page 1',style:Theme.of(c).textTheme.labelLarge),const Divider(height:28),
        SelectableText((preview['page']?['text']??'Aucun texte exploitable').toString()),
        if((preview['questions'] as List? ?? const []).isNotEmpty)...[const SizedBox(height:20),Text('Questions détectées',style:Theme.of(c).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w800)),const SizedBox(height:8),...(preview['questions'] as List).map((q)=>ListTile(leading:const Icon(Icons.help_outline_rounded),title:Text(q['text'].toString())))],
      ]))));
    }catch(e){if(mounted && context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Aperçu indisponible : $e')));}
  }
}

class CreateBatchDialog extends StatefulWidget {
  const CreateBatchDialog({super.key});
  @override State<CreateBatchDialog> createState()=>_CreateBatchDialogState();
}
class _CreateBatchDialogState extends State<CreateBatchDialog>{
  final name=TextEditingController(),faculty=TextEditingController(text:'Médecine'),program=TextEditingController(text:'Médecine humaine'),level=TextEditingController(text:'BAC1'),semester=TextEditingController(text:'S1');
  String kind='course',risk='medical',rights='authorized';
  @override Widget build(BuildContext c)=>AlertDialog(title:const Text('Nouveau lot d’ingestion'),content:SizedBox(width:520,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
    TextField(controller:name,decoration:const InputDecoration(labelText:'Nom du lot',hintText:'BAC1 — Physiologie — Septembre')),
    const SizedBox(height:10),TextField(controller:faculty,decoration:const InputDecoration(labelText:'Faculté / domaine')),const SizedBox(height:10),TextField(controller:program,decoration:const InputDecoration(labelText:'Programme')),const SizedBox(height:10),
    Row(children:[Expanded(child:TextField(controller:level,decoration:const InputDecoration(labelText:'Niveau'))),const SizedBox(width:10),Expanded(child:TextField(controller:semester,decoration:const InputDecoration(labelText:'Semestre')))]),const SizedBox(height:10),
    DropdownButtonFormField(initialValue:kind,decoration:const InputDecoration(labelText:'Type'),items:const[DropdownMenuItem(value:'course',child:Text('Cours')),DropdownMenuItem(value:'assessment',child:Text('Interrogation / examen')),DropdownMenuItem(value:'question_set',child:Text('Banque de questions'))],onChanged:(v)=>setState(()=>kind=v??kind)),const SizedBox(height:10),
    Row(children:[Expanded(child:DropdownButtonFormField(initialValue:risk,decoration:const InputDecoration(labelText:'Risque'),items:const[DropdownMenuItem(value:'standard',child:Text('Standard')),DropdownMenuItem(value:'medical',child:Text('Médical')),DropdownMenuItem(value:'high_stakes',child:Text('High-stakes'))],onChanged:(v)=>setState(()=>risk=v??risk))),const SizedBox(width:10),Expanded(child:DropdownButtonFormField(initialValue:rights,decoration:const InputDecoration(labelText:'Droits'),items:const[DropdownMenuItem(value:'authorized',child:Text('Autorisé')),DropdownMenuItem(value:'internal_only',child:Text('Interne')),DropdownMenuItem(value:'unknown',child:Text('À vérifier'))],onChanged:(v)=>setState(()=>rights=v??rights)))])
  ]))),actions:[TextButton(onPressed:()=>Navigator.pop(c),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(c,{'name':name.text.trim(),'defaults':{'content_kind':kind,'faculty_domain':faculty.text.trim(),'program':program.text.trim(),'level':level.text.trim(),'semester':semester.text.trim().isEmpty?null:semester.text.trim(),'risk':risk,'rights_status':rights,'rights_note':''}}),child:const Text('Créer le lot'))]);
}

class _MetricCard extends StatelessWidget{final IconData icon;final String label,value;final bool danger;const _MetricCard({required this.icon,required this.label,required this.value,this.danger=false});@override Widget build(BuildContext c){final cs=Theme.of(c).colorScheme;return Card(child:Padding(padding:const EdgeInsets.all(16),child:Row(children:[CircleAvatar(backgroundColor:(danger?cs.error:cs.primary).withValues(alpha:.10),foregroundColor:danger?cs.error:cs.primary,child:Icon(icon)),const SizedBox(width:14),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisSize:MainAxisSize.min,children:[Text(value,style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900,color:danger?cs.error:null)),Text(label,maxLines:1,overflow:TextOverflow.ellipsis)]))])));}}
class _StateAvatar extends StatelessWidget{final String state;const _StateAvatar({required this.state});@override Widget build(BuildContext c){final done=['completed','succeeded'].contains(state),bad=['rejected','dead_letter','completed_with_errors'].contains(state);final color=bad?Theme.of(c).colorScheme.error:done?Colors.green:Theme.of(c).colorScheme.primary;return CircleAvatar(backgroundColor:color.withValues(alpha:.12),foregroundColor:color,child:Icon(done?Icons.check_rounded:bad?Icons.priority_high_rounded:Icons.autorenew_rounded));}}
class _Mini extends StatelessWidget{final String label,value;const _Mini({required this.label,required this.value});@override Widget build(BuildContext c)=>Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisSize:MainAxisSize.min,children:[Text(value,style:Theme.of(c).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),Text(label,style:Theme.of(c).textTheme.labelMedium)]);}
class _EmptyPanel extends StatelessWidget{final String message;const _EmptyPanel({this.message='Aucun lot pour le moment. Créez votre premier lot pour commencer.'});@override Widget build(BuildContext c)=>Card(child:Padding(padding:const EdgeInsets.all(32),child:Center(child:Column(children:[const Icon(Icons.inbox_outlined,size:40),const SizedBox(height:10),Text(message,textAlign:TextAlign.center)]))));}
