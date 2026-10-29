import 'dart:async';
import 'package:flutter/material.dart';
import 'editorial_api.dart';

class ContentFactoryPage extends StatefulWidget {
  final EditorialApi api;
  const ContentFactoryPage({super.key, required this.api});
  @override State<ContentFactoryPage> createState() => _ContentFactoryPageState();
}

class _ContentFactoryPageState extends State<ContentFactoryPage> {
  bool loading = true;
  String? error;
  List<dynamic> runs = const [];
  String query = '';
  String stateFilter = 'all';
  String sort = 'recent';
  String? selectedId;
  Map<String, dynamic>? selected;
  bool detailLoading = false;
  Timer? _debounce;

  @override void initState() { super.initState(); _load(); }
  @override void dispose() { _debounce?.cancel(); super.dispose(); }

  Future<void> _load() async {
    setState(() { loading = true; error = null; });
    try {
      final v = await widget.api.factoryRuns();
      if (mounted) setState(() { runs = v; loading = false; });
    } catch (e) {
      if (mounted) setState(() { error = '$e'; loading = false; });
    }
  }

  List<dynamic> get visibleRuns {
    final q = query.trim().toLowerCase();
    final out = runs.where((r) {
      final state = '${r['state'] ?? ''}';
      if (stateFilter != 'all' && state != stateFilter) return false;
      if (q.isEmpty) return true;
      return '${r['id']} ${r['pipeline_version']} $state ${r['quality_score'] ?? ''}'.toLowerCase().contains(q);
    }).toList();
    int score(dynamic r) => (r['quality_score'] as num?)?.toInt() ?? -1;
    if (sort == 'quality') out.sort((a, b) => score(b).compareTo(score(a)));
    if (sort == 'risk') out.sort((a, b) => score(a).compareTo(score(b)));
    return out;
  }

  Future<void> _openRun(String id, {required bool inline}) async {
    setState(() { selectedId = id; detailLoading = true; });
    try {
      final d = await widget.api.factoryRun(id);
      if (!mounted) return;
      setState(() { selected = d; detailLoading = false; });
      if (!inline) {
        await showModalBottomSheet(context: context, isScrollControlled: true, useSafeArea: true,
          builder: (_) => _RunReviewWorkspace(data: d));
      }
    } catch (e) {
      if (mounted) setState(() { detailLoading = false; error = '$e'; });
    }
  }

  @override Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final desktop = width >= 1180;
    final compact = width < 700;
    final ready = runs.where((r) => r['state'] == 'ready_for_review').length;
    final failed = runs.where((r) => r['state'] == 'failed').length;
    final active = runs.where((r) => r['state'] == 'processing' || r['state'] == 'queued').length;
    final scored = runs.where((r) => r['quality_score'] is num).toList();
    final avg = scored.isEmpty ? null : scored.map((r) => (r['quality_score'] as num).toDouble()).reduce((a,b)=>a+b) / scored.length;

    return RefreshIndicator(
      onRefresh: _load,
      child: CustomScrollView(slivers: [
        SliverPadding(padding: EdgeInsets.fromLTRB(compact ? 16 : 24, 22, compact ? 16 : 24, 10), sliver: SliverToBoxAdapter(child: _HeroHeader(active: active))),
        SliverPadding(padding: EdgeInsets.symmetric(horizontal: compact ? 16 : 24), sliver: SliverToBoxAdapter(child: _KpiGrid(total: runs.length, active: active, ready: ready, failed: failed, average: avg))),
        SliverPadding(padding: EdgeInsets.fromLTRB(compact ? 16 : 24, 18, compact ? 16 : 24, 10), sliver: SliverToBoxAdapter(child: _Toolbar(
          query: query, state: stateFilter, sort: sort,
          onQuery: (v) { _debounce?.cancel(); _debounce = Timer(const Duration(milliseconds: 180), () { if (mounted) setState(() => query = v); }); },
          onState: (v) => setState(() => stateFilter = v), onSort: (v) => setState(() => sort = v), onRefresh: _load,
        ))),
        if (error != null) SliverPadding(padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 6), sliver: SliverToBoxAdapter(child: _Notice(icon: Icons.cloud_off_rounded, title: 'Connexion interrompue', text: 'Impossible de synchroniser la Content Factory. $error', action: _load))),
        if (loading) const SliverFillRemaining(hasScrollBody: false, child: Center(child: CircularProgressIndicator()))
        else if (runs.isEmpty) SliverFillRemaining(hasScrollBody: false, child: _EmptyFactory(onRefresh: _load))
        else if (visibleRuns.isEmpty) const SliverFillRemaining(hasScrollBody: false, child: _NoResults())
        else SliverPadding(padding: EdgeInsets.fromLTRB(compact ? 16 : 24, 0, compact ? 16 : 24, 32), sliver: SliverToBoxAdapter(child: desktop
          ? SizedBox(height: 680, child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Expanded(flex: 5, child: _RunList(runs: visibleRuns, selectedId: selectedId, onOpen: (id) => _openRun(id, inline: true))),
              const SizedBox(width: 16),
              Expanded(flex: 7, child: _DesktopDetail(data: selected, loading: detailLoading)),
            ]))
          : _RunList(runs: visibleRuns, selectedId: selectedId, onOpen: (id) => _openRun(id, inline: false)))),
      ]),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  final int active; const _HeroHeader({required this.active});
  @override Widget build(BuildContext context) => Semantics(header: true, child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Container(width: 48, height: 48, decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(15)), child: Icon(Icons.precision_manufacturing_rounded, color: Theme.of(context).colorScheme.onPrimaryContainer)),
    const SizedBox(width: 14),
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Content Factory', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 5),
      Text('Poste de contrôle éditorial · source → artefacts pédagogiques → preuves → revue humaine', style: Theme.of(context).textTheme.bodyMedium),
      const SizedBox(height: 10),
      Wrap(spacing: 8, runSpacing: 8, children: [
        const _Pill(icon: Icons.lock_outline_rounded, text: 'Aucune publication automatique'),
        const _Pill(icon: Icons.link_rounded, text: 'Provenance page par page'),
        if (active > 0) _Pill(icon: Icons.sync_rounded, text: '$active run${active > 1 ? 's' : ''} actif${active > 1 ? 's' : ''}'),
      ])
    ])),
  ]));
}

class _Pill extends StatelessWidget { final IconData icon; final String text; const _Pill({required this.icon, required this.text});
  @override Widget build(BuildContext c) => Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7), decoration: BoxDecoration(border: Border.all(color: Theme.of(c).colorScheme.outlineVariant), borderRadius: BorderRadius.circular(99)), child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon,size:16),const SizedBox(width:6),Text(text,style:Theme.of(c).textTheme.labelMedium)])); }

class _KpiGrid extends StatelessWidget {
  final int total, active, ready, failed; final double? average;
  const _KpiGrid({required this.total, required this.active, required this.ready, required this.failed, required this.average});
  @override Widget build(BuildContext c) { final w=MediaQuery.sizeOf(c).width; final cols=w>=1250?5:w>=760?3:2; return GridView.count(crossAxisCount:cols,shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),mainAxisSpacing:10,crossAxisSpacing:10,childAspectRatio:w<500?1.55:2.15,children:[
    _Kpi('Runs','$total',Icons.inventory_2_outlined,'Corpus traité'), _Kpi('En production','$active',Icons.settings_suggest_rounded,'Pipeline actif'), _Kpi('Prêts à relire','$ready',Icons.fact_check_outlined,'Action humaine'), _Kpi('Bloqués','$failed',Icons.report_gmailerrorred_rounded,'À diagnostiquer'), _Kpi('Qualité moyenne',average==null?'—':'${average!.round()}/100',Icons.analytics_outlined,'Runs scorés'),
  ]); }
}
class _Kpi extends StatelessWidget { final String label,value,caption; final IconData icon; const _Kpi(this.label,this.value,this.icon,this.caption);
  @override Widget build(BuildContext c)=>Card(clipBehavior:Clip.antiAlias,child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisAlignment:MainAxisAlignment.center,children:[Icon(icon,size:21),const Spacer(),Text(value,style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),Text(label,style:const TextStyle(fontWeight:FontWeight.w700),maxLines:1,overflow:TextOverflow.ellipsis),Text(caption,style:Theme.of(c).textTheme.bodySmall,maxLines:1,overflow:TextOverflow.ellipsis)]))); }

class _Toolbar extends StatelessWidget {
  final String query,state,sort; final ValueChanged<String> onQuery,onState,onSort; final Future<void> Function() onRefresh;
  const _Toolbar({required this.query,required this.state,required this.sort,required this.onQuery,required this.onState,required this.onSort,required this.onRefresh});
  @override Widget build(BuildContext c)=>LayoutBuilder(builder:(c,k){final narrow=k.maxWidth<760;final search=TextField(onChanged:onQuery,decoration:const InputDecoration(prefixIcon:Icon(Icons.search_rounded),hintText:'Rechercher un run, état, pipeline…',border:OutlineInputBorder()));final filters=Wrap(spacing:8,runSpacing:8,children:[
    _Choice(label:'Tous',selected:state=='all',onTap:()=>onState('all')),_Choice(label:'À relire',selected:state=='ready_for_review',onTap:()=>onState('ready_for_review')),_Choice(label:'Actifs',selected:state=='processing',onTap:()=>onState('processing')),_Choice(label:'Bloqués',selected:state=='failed',onTap:()=>onState('failed')),
    PopupMenuButton<String>(tooltip:'Trier',initialValue:sort,onSelected:onSort,itemBuilder:(_)=>const [PopupMenuItem(value:'recent',child:Text('Plus récents')),PopupMenuItem(value:'quality',child:Text('Qualité décroissante')),PopupMenuItem(value:'risk',child:Text('Qualité à surveiller'))],child:Chip(avatar:const Icon(Icons.sort_rounded,size:18),label:Text(sort=='quality'?'Meilleure qualité':sort=='risk'?'À surveiller':'Plus récents'))),
    IconButton.filledTonal(tooltip:'Actualiser',onPressed:onRefresh,icon:const Icon(Icons.refresh_rounded)),
  ]);return narrow?Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[search,const SizedBox(height:10),filters]):Row(children:[Expanded(child:search),const SizedBox(width:12),Flexible(child:filters)]);});
}
class _Choice extends StatelessWidget {final String label;final bool selected;final VoidCallback onTap;const _Choice({required this.label,required this.selected,required this.onTap});@override Widget build(BuildContext c)=>FilterChip(label:Text(label),selected:selected,onSelected:(_)=>onTap());}

class _RunList extends StatelessWidget {
  final List<dynamic> runs; final String? selectedId; final ValueChanged<String> onOpen;
  const _RunList({required this.runs,required this.selectedId,required this.onOpen});
  @override Widget build(BuildContext c)=>ListView.separated(shrinkWrap:true,physics:MediaQuery.sizeOf(c).width>=1180?const AlwaysScrollableScrollPhysics():const NeverScrollableScrollPhysics(),itemCount:runs.length,separatorBuilder:(_,__)=>const SizedBox(height:8),itemBuilder:(_,i){final r=runs[i] as Map<String,dynamic>;final id='${r['id']}';return _RunCard(data:r,selected:selectedId==id,onTap:()=>onOpen(id));});
}
class _RunCard extends StatelessWidget {final Map<String,dynamic> data;final bool selected;final VoidCallback onTap;const _RunCard({required this.data,required this.selected,required this.onTap});
  @override Widget build(BuildContext c){final state='${data['state']??'unknown'}';final score=(data['quality_score'] as num?)?.toInt();final label=_stateLabel(state);final icon=_stateIcon(state);return Semantics(button:true,label:'Run ${_short(data['id'])}, $label, qualité ${score??'non évaluée'}',child:Card(elevation:selected?1:0,shape:RoundedRectangleBorder(side:BorderSide(color:selected?Theme.of(c).colorScheme.primary:Theme.of(c).colorScheme.outlineVariant,width:selected?2:1),borderRadius:BorderRadius.circular(14)),child:InkWell(borderRadius:BorderRadius.circular(14),onTap:onTap,child:Padding(padding:const EdgeInsets.all(14),child:Row(children:[
    Container(width:42,height:42,decoration:BoxDecoration(color:Theme.of(c).colorScheme.surfaceContainerHighest,borderRadius:BorderRadius.circular(12)),child:Icon(icon)),const SizedBox(width:12),
    Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Expanded(child:Text('Run ${_short(data['id'])}',style:const TextStyle(fontWeight:FontWeight.w800))),_Status(label:label)]),const SizedBox(height:6),Text('${data['pipeline_version']??'pipeline —'}',style:Theme.of(c).textTheme.bodySmall),const SizedBox(height:8),Row(children:[Expanded(child:LinearProgressIndicator(value:score==null?0:score/100,minHeight:6,borderRadius:BorderRadius.circular(99))),const SizedBox(width:10),Text(score==null?'—':'$score/100',style:const TextStyle(fontWeight:FontWeight.w700))])])),const SizedBox(width:6),const Icon(Icons.chevron_right_rounded)
  ]))))); }
}

class _DesktopDetail extends StatelessWidget {final Map<String,dynamic>? data;final bool loading;const _DesktopDetail({required this.data,required this.loading});@override Widget build(BuildContext c)=>Card(clipBehavior:Clip.antiAlias,child:loading?const Center(child:CircularProgressIndicator()):data==null?const Center(child:Padding(padding:EdgeInsets.all(30),child:Column(mainAxisSize:MainAxisSize.min,children:[Icon(Icons.touch_app_outlined,size:42),SizedBox(height:12),Text('Sélectionnez un run',style:TextStyle(fontWeight:FontWeight.w800)),SizedBox(height:5),Text('La revue source ↔ production s’ouvrira ici.')]))):_RunReviewWorkspace(data:data!,embedded:true));}

class _RunReviewWorkspace extends StatefulWidget {final Map<String,dynamic> data;final bool embedded;const _RunReviewWorkspace({required this.data,this.embedded=false});@override State<_RunReviewWorkspace> createState()=>_RunReviewWorkspaceState();}
class _RunReviewWorkspaceState extends State<_RunReviewWorkspace>{int tab=0;String assetFilter='all';
  @override Widget build(BuildContext c){final assets=(widget.data['assets'] as List<dynamic>? ?? const []);final gates=(widget.data['quality_gates'] as List<dynamic>? ?? const []);final evidence=(widget.data['evidence'] as List<dynamic>? ?? const []);final evByAsset={for(final e in evidence)e['asset_id']:e};final kinds=assets.map((a)=>'${a['kind']}').toSet().toList();final filtered=assetFilter=='all'?assets:assets.where((a)=>a['kind']==assetFilter).toList();final body=Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
    _ReviewHeader(data:widget.data,assets:assets.length,evidence:evidence.length),
    Padding(padding:const EdgeInsets.fromLTRB(18,10,18,0),child:SegmentedButton<int>(segments:const [ButtonSegment(value:0,icon:Icon(Icons.compare_arrows_rounded),label:Text('Artefacts')),ButtonSegment(value:1,icon:Icon(Icons.fact_check_outlined),label:Text('Qualité')),ButtonSegment(value:2,icon:Icon(Icons.info_outline_rounded),label:Text('Traçabilité'))],selected:{tab},onSelectionChanged:(v)=>setState(()=>tab=v.first),showSelectedIcon:false)),
    const SizedBox(height:8),Expanded(child:tab==0?_ArtifactsView(assets:filtered,evidence:evByAsset,kinds:kinds,filter:assetFilter,onFilter:(v)=>setState(()=>assetFilter=v)):tab==1?_GatesView(gates:gates):_TraceView(data:widget.data,evidence:evidence)),
  ]);return widget.embedded?body:DraggableScrollableSheet(expand:false,initialChildSize:.92,maxChildSize:.98,minChildSize:.6,builder:(_,__)=>body);}}

class _ReviewHeader extends StatelessWidget{final Map<String,dynamic> data;final int assets,evidence;const _ReviewHeader({required this.data,required this.assets,required this.evidence});@override Widget build(BuildContext c){final score=(data['quality_score'] as num?)?.toInt();return Container(padding:const EdgeInsets.fromLTRB(20,18,20,12),decoration:BoxDecoration(border:Border(bottom:BorderSide(color:Theme.of(c).colorScheme.outlineVariant))),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Dossier ${_short(data['id'])}',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:4),Text('$assets artefacts · $evidence preuves · ${data['pipeline_version']??'pipeline —'}')])),_Status(label:_stateLabel('${data['state']}'))]),const SizedBox(height:12),Row(children:[Icon(Icons.shield_outlined,size:18),const SizedBox(width:6),Text('Qualité ${score??'—'}/100',style:const TextStyle(fontWeight:FontWeight.w800)),const SizedBox(width:14),const Icon(Icons.person_outline_rounded,size:18),const SizedBox(width:5),const Expanded(child:Text('Validation humaine obligatoire avant publication',maxLines:1,overflow:TextOverflow.ellipsis))]) ]));}}

class _ArtifactsView extends StatelessWidget{final List<dynamic> assets;final Map<dynamic,dynamic> evidence;final List<String> kinds;final String filter;final ValueChanged<String> onFilter;const _ArtifactsView({required this.assets,required this.evidence,required this.kinds,required this.filter,required this.onFilter});@override Widget build(BuildContext c)=>ListView(padding:const EdgeInsets.all(18),children:[Wrap(spacing:7,runSpacing:7,children:[_Choice(label:'Tous',selected:filter=='all',onTap:()=>onFilter('all')),...kinds.map((k)=>_Choice(label:k,selected:filter==k,onTap:()=>onFilter(k)))]),const SizedBox(height:12),if(assets.isEmpty)const _InlineEmpty('Aucun artefact pour ce filtre.') else ...assets.map((a){final ev=evidence[a['id']];return Card(margin:const EdgeInsets.only(bottom:10),child:ExpansionTile(leading:const Icon(Icons.article_outlined),title:Text(a['title']??'Sans titre',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${a['kind']} · confiance ${(((a['confidence']??0) as num)*100).round()}%'),childrenPadding:const EdgeInsets.fromLTRB(16,0,16,16),children:[if(a['content']!=null)...[Align(alignment:Alignment.centerLeft,child:SelectableText('${a['content']}')),const SizedBox(height:12)],if(ev!=null)Container(width:double.infinity,padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:Theme.of(c).colorScheme.surfaceContainerHighest,borderRadius:BorderRadius.circular(12)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[const Icon(Icons.menu_book_outlined,size:18),const SizedBox(width:6),Text('Preuve source · p. ${ev['page_start']}–${ev['page_end']}',style:const TextStyle(fontWeight:FontWeight.w800))]),const SizedBox(height:7),SelectableText(ev['quote']??'Aucun extrait')]))else const _NoticeCompact('Preuve source indisponible — à vérifier avant validation.')]));})] );}

class _GatesView extends StatelessWidget{final List<dynamic> gates;const _GatesView({required this.gates});@override Widget build(BuildContext c){final failed=gates.where((g)=>g['passed']!=true).length;return ListView(padding:const EdgeInsets.all(18),children:[_NoticeCompact(failed==0?'Tous les contrôles enregistrés sont satisfaits. La revue humaine reste obligatoire.':'$failed contrôle${failed>1?'s':''} nécessite${failed>1?'nt':''} une attention humaine.'),const SizedBox(height:10),...gates.map((g)=>Card(child:ListTile(leading:Icon(g['passed']==true?Icons.check_circle_outline_rounded:Icons.error_outline_rounded),title:Text('${g['code']}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${g['detail']??''}'),trailing:Text(g['passed']==true?'PASS':'CHECK',style:const TextStyle(fontWeight:FontWeight.w800))))) ]);}}
class _TraceView extends StatelessWidget{final Map<String,dynamic> data;final List<dynamic> evidence;const _TraceView({required this.data,required this.evidence});@override Widget build(BuildContext c)=>ListView(padding:const EdgeInsets.all(18),children:[const _NoticeCompact('Chaîne de preuve conservée pour audit. Les sorties de la Factory ne constituent jamais une autorisation de publication.'),const SizedBox(height:12),_Meta('Run','${data['id']??'—'}'),_Meta('Pipeline','${data['pipeline_version']??'—'}'),_Meta('État',_stateLabel('${data['state']}')),_Meta('Score qualité','${data['quality_score']??'—'}/100'),_Meta('Preuves','${evidence.length}'),if(data['source_sha256']!=null)_Meta('SHA-256 source','${data['source_sha256']}')]);}
class _Meta extends StatelessWidget{final String k,v;const _Meta(this.k,this.v);@override Widget build(BuildContext c)=>Padding(padding:const EdgeInsets.symmetric(vertical:7),child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[SizedBox(width:130,child:Text(k,style:Theme.of(c).textTheme.labelLarge)),Expanded(child:SelectableText(v))]));}

class _Status extends StatelessWidget{final String label;const _Status({required this.label});@override Widget build(BuildContext c)=>Container(padding:const EdgeInsets.symmetric(horizontal:9,vertical:5),decoration:BoxDecoration(color:Theme.of(c).colorScheme.secondaryContainer,borderRadius:BorderRadius.circular(99)),child:Text(label,style:Theme.of(c).textTheme.labelSmall?.copyWith(fontWeight:FontWeight.w800)));}
class _Notice extends StatelessWidget{final IconData icon;final String title,text;final Future<void> Function() action;const _Notice({required this.icon,required this.title,required this.text,required this.action});@override Widget build(BuildContext c)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Row(children:[Icon(icon),const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(title,style:const TextStyle(fontWeight:FontWeight.w800)),Text(text)])),TextButton(onPressed:action,child:const Text('Réessayer'))])));}
class _NoticeCompact extends StatelessWidget{final String text;const _NoticeCompact(this.text);@override Widget build(BuildContext c)=>Container(width:double.infinity,padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:Theme.of(c).colorScheme.surfaceContainerHighest,borderRadius:BorderRadius.circular(12)),child:Text(text));}
class _InlineEmpty extends StatelessWidget{final String text;const _InlineEmpty(this.text);@override Widget build(BuildContext c)=>Padding(padding:const EdgeInsets.all(24),child:Center(child:Text(text)));}
class _EmptyFactory extends StatelessWidget{final Future<void> Function() onRefresh;const _EmptyFactory({required this.onRefresh});@override Widget build(BuildContext c)=>Center(child:Padding(padding:const EdgeInsets.all(28),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.precision_manufacturing_outlined,size:54),const SizedBox(height:14),Text('La chaîne est prête',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:7),const Text('Aucun run pour le moment. Lancez une transformation depuis un document dont l’ingestion est terminée.',textAlign:TextAlign.center),const SizedBox(height:14),FilledButton.tonalIcon(onPressed:onRefresh,icon:const Icon(Icons.refresh_rounded),label:const Text('Actualiser'))])));}
class _NoResults extends StatelessWidget{const _NoResults();@override Widget build(BuildContext c)=>const Center(child:Padding(padding:EdgeInsets.all(28),child:Column(mainAxisSize:MainAxisSize.min,children:[Icon(Icons.search_off_rounded,size:44),SizedBox(height:10),Text('Aucun run ne correspond aux filtres.',style:TextStyle(fontWeight:FontWeight.w800))])));}

String _short(dynamic id){final s='$id';return s.length<=8?s:s.substring(0,8);}
String _stateLabel(String s)=>switch(s){'ready_for_review'=>'Prêt à relire','processing'=>'En production','queued'=>'En attente','failed'=>'Bloqué','cancelled'=>'Annulé','completed'=>'Terminé',_=>s.replaceAll('_',' ')};
IconData _stateIcon(String s)=>switch(s){'ready_for_review'=>Icons.fact_check_rounded,'processing'=>Icons.settings_suggest_rounded,'queued'=>Icons.schedule_rounded,'failed'=>Icons.warning_amber_rounded,'cancelled'=>Icons.cancel_outlined,_=>Icons.precision_manufacturing_outlined};
