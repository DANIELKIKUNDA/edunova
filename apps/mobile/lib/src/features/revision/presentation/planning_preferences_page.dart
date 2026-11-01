import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../../study_plan/application/adaptive_planning_repository.dart';
import '../../study_plan/domain/adaptive_planning.dart';

class PlanningPreferencesPage extends ConsumerStatefulWidget {
  const PlanningPreferencesPage({super.key});
  @override ConsumerState<PlanningPreferencesPage> createState()=>_PlanningPreferencesPageState();
}

class _PlanningPreferencesPageState extends ConsumerState<PlanningPreferencesPage> {
  PlanningPreferences _value=const PlanningPreferences();
  bool _loading=true;
  @override void initState(){super.initState();Future.microtask(_load);}
  Future<void> _load() async {final v=await ref.read(adaptivePlanningRepositoryProvider).loadPreferences();if(mounted)setState((){_value=v;_loading=false;});}

  @override Widget build(BuildContext context){
    final rules=ref.watch(studyAvailabilityProvider);
    return Scaffold(
      appBar:AppBar(title:const Text('Planning intelligent')),
      body:_loading?const Center(child:CircularProgressIndicator()):ListView(padding:const EdgeInsets.fromLTRB(18,8,18,40),children:[
        _Header(value:_value),
        const SizedBox(height:18),
        _SliderCard(title:'Objectif de préparation',value:_value.targetReadiness.toDouble(),min:60,max:100,suffix:'%',onChanged:(v)=>setState(()=>_value=PlanningPreferences(
          dailyBudgetMinutes:_value.dailyBudgetMinutes,maxNotificationsPerDay:_value.maxNotificationsPerDay,quietStartMinute:_value.quietStartMinute,quietEndMinute:_value.quietEndMinute,
          maxContinuousMinutes:_value.maxContinuousMinutes,breakMinutes:_value.breakMinutes,maxCoursesPerDay:_value.maxCoursesPerDay,maxCourseSwitches:_value.maxCourseSwitches,
          targetReadiness:v.round(),planningHorizonDays:_value.planningHorizonDays))),
        _SliderCard(title:'Travail continu maximum',value:_value.maxContinuousMinutes.toDouble(),min:20,max:90,suffix:' min',onChanged:(v)=>setState(()=>_value=_copy(maxContinuousMinutes:v.round()))),
        _SliderCard(title:'Pause automatique',value:_value.breakMinutes.toDouble(),min:5,max:25,suffix:' min',onChanged:(v)=>setState(()=>_value=_copy(breakMinutes:v.round()))),
        _SliderCard(title:'Horizon du planning',value:_value.planningHorizonDays.toDouble(),min:7,max:30,suffix:' jours',onChanged:(v)=>setState(()=>_value=_copy(planningHorizonDays:v.round()))),
        const SizedBox(height:14),
        Row(children:[Expanded(child:Text('Mes plages d’étude',style:Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight:FontWeight.w900))),IconButton(onPressed:_addRule,icon:const Icon(Icons.add_circle_rounded))]),
        const SizedBox(height:6),
        rules.when(loading:()=>const LinearProgressIndicator(),error:(e,_)=>Text(e.toString()),data:(rows)=>rows.isEmpty?const _EmptyAvailability():Column(children:rows.map((r)=>_AvailabilityTile(rule:r,onDelete:()=>ref.read(adaptivePlanningRepositoryProvider).deleteAvailabilityRule(r.id))).toList())),
        const SizedBox(height:24),
        FilledButton.icon(onPressed:_save,icon:const Icon(Icons.check_rounded),label:const Text('Enregistrer mes préférences')),
      ]),
    );
  }

  PlanningPreferences _copy({int? maxContinuousMinutes,int? breakMinutes,int? planningHorizonDays})=>PlanningPreferences(
    dailyBudgetMinutes:_value.dailyBudgetMinutes,maxNotificationsPerDay:_value.maxNotificationsPerDay,quietStartMinute:_value.quietStartMinute,quietEndMinute:_value.quietEndMinute,
    maxContinuousMinutes:maxContinuousMinutes??_value.maxContinuousMinutes,breakMinutes:breakMinutes??_value.breakMinutes,maxCoursesPerDay:_value.maxCoursesPerDay,maxCourseSwitches:_value.maxCourseSwitches,
    targetReadiness:_value.targetReadiness,planningHorizonDays:planningHorizonDays??_value.planningHorizonDays,
  );

  Future<void> _save() async {await ref.read(adaptivePlanningRepositoryProvider).savePreferences(_value);if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Préférences enregistrées.')));}

  Future<void> _addRule() async {
    int weekday=DateTime.now().weekday.clamp(1,7).toInt();int start=18*60;int end=20*60;EnergyLevel energy=EnergyLevel.medium;
    final ok=await showDialog<bool>(context:context,builder:(context)=>StatefulBuilder(builder:(context,setState)=>AlertDialog(
      title:const Text('Ajouter une plage d’étude'),content:Column(mainAxisSize:MainAxisSize.min,children:[
        DropdownButtonFormField(initialValue:weekday,items:List.generate(7,(i)=>DropdownMenuItem(value:i+1,child:Text(['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'][i]))),onChanged:(v)=>setState(()=>weekday=v!),decoration:const InputDecoration(labelText:'Jour')),
        const SizedBox(height:10),
        Row(children:[Expanded(child:TextFormField(initialValue:'18:00',decoration:const InputDecoration(labelText:'Début'),onChanged:(v)=>start=_parse(v,start))),const SizedBox(width:10),Expanded(child:TextFormField(initialValue:'20:00',decoration:const InputDecoration(labelText:'Fin'),onChanged:(v)=>end=_parse(v,end)))]),
        const SizedBox(height:10),
        DropdownButtonFormField(initialValue:energy,items:EnergyLevel.values.map((e)=>DropdownMenuItem(value:e,child:Text(switch(e){EnergyLevel.low=>'Énergie faible',EnergyLevel.medium=>'Énergie normale',EnergyLevel.high=>'Énergie élevée'}))).toList(),onChanged:(v)=>setState(()=>energy=v!),decoration:const InputDecoration(labelText:'Niveau d’énergie habituel')),
      ]),actions:[TextButton(onPressed:()=>Navigator.pop(context,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(context,true),child:const Text('Ajouter'))])));
    if(ok==true&&end>start){await ref.read(adaptivePlanningRepositoryProvider).saveAvailabilityRule(AvailabilityRule(id:const Uuid().v4(),weekday:weekday,startMinute:start,endMinute:end,energy:energy));}
  }
  int _parse(String v,int fallback){final p=v.split(':');if(p.length!=2)return fallback;final h=int.tryParse(p[0]);final m=int.tryParse(p[1]);if(h==null||m==null||h<0||h>23||m<0||m>59)return fallback;return h*60+m;}
}

class _Header extends StatelessWidget{const _Header({required this.value});final PlanningPreferences value;@override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(20),child:Row(children:[const CircleAvatar(radius:26,child:Icon(Icons.tune_rounded)),const SizedBox(width:14),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Un planning qui respecte ton rythme',style:Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:4),Text('Objectif ${value.targetReadiness}% · horizon ${value.planningHorizonDays} jours · pause ${value.breakMinutes} min')]))])));}
class _SliderCard extends StatelessWidget{const _SliderCard({required this.title,required this.value,required this.min,required this.max,required this.suffix,required this.onChanged});final String title,suffix;final double value,min,max;final ValueChanged<double> onChanged;@override Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.fromLTRB(18,14,18,10),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Expanded(child:Text(title,style:const TextStyle(fontWeight:FontWeight.w800))),Text('${value.round()}$suffix',style:TextStyle(fontWeight:FontWeight.w900,color:Theme.of(context).colorScheme.primary))]),Slider(value:value.clamp(min,max).toDouble(),min:min,max:max,divisions:(max-min).round(),onChanged:onChanged)])));}
class _AvailabilityTile extends StatelessWidget{const _AvailabilityTile({required this.rule,required this.onDelete});final AvailabilityRule rule;final VoidCallback onDelete;@override Widget build(BuildContext context){String hm(int m)=>'${(m~/60).toString().padLeft(2,'0')}:${(m%60).toString().padLeft(2,'0')}';final day=['','Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][rule.weekday];return Card(child:ListTile(leading:CircleAvatar(child:Text(day)),title:Text('${hm(rule.startMinute)} – ${hm(rule.endMinute)}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('Énergie ${rule.energy.name}'),trailing:IconButton(onPressed:onDelete,icon:const Icon(Icons.delete_outline_rounded))));}}
class _EmptyAvailability extends StatelessWidget{const _EmptyAvailability();@override Widget build(BuildContext context)=>const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Ajoute tes créneaux habituels. EduNova retirera automatiquement les heures déjà occupées par tes cours.')));}
