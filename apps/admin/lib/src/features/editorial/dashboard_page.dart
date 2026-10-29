import 'package:flutter/material.dart';
import 'editorial_api.dart';
import 'studio_widgets.dart';

class EditorialDashboardPage extends StatefulWidget{
  final EditorialApi api;final ValueChanged<int> onOpenSection;const EditorialDashboardPage({super.key,required this.api,required this.onOpenSection});
  @override State<EditorialDashboardPage> createState()=>_EditorialDashboardPageState();
}
class _EditorialDashboardPageState extends State<EditorialDashboardPage>{late Future<Map<String,dynamic>> _future;
  @override void initState(){super.initState();_future=widget.api.dashboard();}
  void _reload()=>setState(()=>_future=widget.api.dashboard());
  @override Widget build(BuildContext context)=>FutureBuilder<Map<String,dynamic>>(future:_future,builder:(context,s){
    if(s.connectionState!=ConnectionState.done)return const Center(child:CircularProgressIndicator());
    if(s.hasError)return StudioErrorState(onRetry:_reload,message:s.error.toString());
    final d=s.data!;final counts=(d['counts']??{}) as Map<String,dynamic>;
    final metrics=[
      ('${d['needs_review']??0}','À relire',Icons.fact_check_outlined,Colors.indigo,2),
      ('${d['changes_requested']??0}','Corrections demandées',Icons.edit_note_rounded,Colors.orange,1),
      ('${d['approved_to_publish']??0}','Prêts à publier',Icons.publish_outlined,Colors.teal,3),
      ('${d['overdue_assignments']??0}','Affectations en retard',Icons.schedule_rounded,Colors.red,1),
    ];
    return RefreshIndicator(onRefresh:()async=>_reload(),child:ListView(padding:const EdgeInsets.all(24),children:[
      Wrap(alignment:WrapAlignment.spaceBetween,crossAxisAlignment:WrapCrossAlignment.center,runSpacing:10,children:[
        Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Bonsoir${widget.api.displayName.isNotEmpty?' ${widget.api.displayName}':''} 👋',style:Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight:FontWeight.w800)),const SizedBox(height:4),Text('Voici l’état réel de la chaîne éditoriale EduNova.',style:Theme.of(context).textTheme.bodyLarge)]),
        FilledButton.tonalIcon(onPressed:_reload,icon:const Icon(Icons.refresh),label:const Text('Actualiser')),
      ]),const SizedBox(height:24),
      LayoutBuilder(builder:(context,c){final cols=c.maxWidth>=1100?4:c.maxWidth>=650?2:1;final width=(c.maxWidth-(cols-1)*14)/cols;return Wrap(spacing:14,runSpacing:14,children:[for(final m in metrics)SizedBox(width:width,child:MetricCard(value:m.$1,label:m.$2,icon:m.$3,color:m.$4,onTap:()=>widget.onOpenSection(m.$5))) ]);}),
      const SizedBox(height:24),
      LayoutBuilder(builder:(context,c){final wide=c.maxWidth>=900;final workflow=StudioSection(title:'Flux éditorial',subtitle:'Chaque contenu avance par étapes contrôlées.',child:Column(children:[_Flow('1','Brouillon','Édition, provenance et droits.'),_Flow('2','Relecture','Checklist qualité + sources vérifiées.'),_Flow('3','Approuvé','Prêt pour une publication contrôlée.'),_Flow('4','Publié','Version immuable visible dans la bibliothèque.') ]));
        final health=StudioSection(title:'Santé de la production',subtitle:'Signaux à surveiller avant qu’ils deviennent des retards.',child:Column(children:[_Line('Total contenus','${d['total']??0}'),_Line('Affectations actives','${d['active_assignments']??0}'),_Line('Mes affectations','${d['my_assignments']??0}'),_Line('Publiés','${counts['published']??0}'),_Line('Archivés','${counts['archived']??0}') ]));
        if(!wide)return Column(children:[workflow,const SizedBox(height:14),health]);return Row(crossAxisAlignment:CrossAxisAlignment.start,children:[Expanded(child:workflow),const SizedBox(width:14),Expanded(child:health)]);
      }),
      const SizedBox(height:100),
    ]));
  });}
class _Flow extends StatelessWidget{final String n,title,subtitle;const _Flow(this.n,this.title,this.subtitle);@override Widget build(BuildContext c)=>Padding(padding:const EdgeInsets.symmetric(vertical:8),child:Row(children:[CircleAvatar(radius:16,child:Text(n)),const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(title,style:Theme.of(c).textTheme.titleSmall?.copyWith(fontWeight:FontWeight.w700)),Text(subtitle,style:Theme.of(c).textTheme.bodySmall)]))]));}
class _Line extends StatelessWidget{final String k,v;const _Line(this.k,this.v);@override Widget build(BuildContext c)=>Padding(padding:const EdgeInsets.symmetric(vertical:8),child:Row(children:[Expanded(child:Text(k)),Text(v,style:Theme.of(c).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w800))]));}
